# mlib_download.py
# WeasyPrint HTML-to-PDF 下载器 - Class 版本（支持无限次复用 + 永久缓存）
# 新增：多次复用支持（add_task → start_tasks → 继续 add_task → start_tasks...）
# 缓存（URL/图片/字体）跨批次永久保留，任务队列每次执行后自动清空

import os
import gc
import time
import tempfile
import pathlib
import threading
from collections.abc import MutableMapping
from typing import Any, Dict, List, Optional, Tuple

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from weasyprint.urls import URLFetcher, URLFetcherResponse


class CachedURLFetcher(URLFetcher):
    """内部缓存 fetcher（每个实例独立，但跨批次持久）"""
    def __init__(self, cache: MutableMapping[str, URLFetcherResponse]):
        super().__init__()
        self.cache = cache

    def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> URLFetcherResponse:
        # 极速命中路径
        if url in self.cache:
            return self.cache[url].copy()

        # 发起真实获取
        response: URLFetcherResponse = super().fetch(url, headers=headers)
        
        # 【关键修复】：WeasyPrint 的默认 fetcher 经常返回带有 'file_obj' 的字典。
        # 如果我们直接缓存这个字典，WeasyPrint 在第一次渲染结束后会关闭该 file_obj。
        # 导致第二次命中缓存时抛出 "I/O operation on closed file"。
        # 修复：存入缓存前，必须读取流内容并转为 bytes (string 字段)，然后关闭并删除 file_obj。
        if response and 'file_obj' in response and 'string' not in response:
            try:
                response['string'] = response['file_obj'].read()
            finally:
                try:
                    response['file_obj'].close()
                except Exception:
                    pass
            del response['file_obj']

        self.cache[url] = response
        return response.copy()


class MlibDownloader:
    """
    WeasyPrint 下载器类（支持无限次复用）
    - 初始化一次即可，之后反复 add_task + start_tasks
    - 每次 start_tasks 后自动清空任务队列，缓存永久保留（适合纯静态页面）
    - 对象销毁时自动输出最终缓存日志
    """

    def __init__(self, default_base_url: Optional[str] = None):
        """
        初始化函数（只需调用一次）
        :param default_base_url: 全局默认资源根目录（相对/绝对均可）
        """
        self.default_base_url = default_base_url
        self._task_list: List[Tuple[str, str, Optional[str]]] = []

        # 【WeasyPrint 60.0+ 适配】：使用磁盘临时目录作为图片缓存，防止内存溢出
        # 在 68.1+ 中，参数名为 cache，类型可以是 dict 或 路径字符串
        self._image_cache_dir = tempfile.TemporaryDirectory()
        self._image_cache = self._image_cache_dir.name

        # 实例级永久缓存（多次复用关键）
        self._url_cache: Dict[str, URLFetcherResponse] = {}
        self._font_config = FontConfiguration()
        self._fetcher = CachedURLFetcher(self._url_cache)

        self._PAGE_CSS = CSS(string="""
        @page {
            size: A4 portrait;
            margin-top: 1cm;
            margin-bottom: 1cm;
            margin-left: 0.75cm;
            margin-right: 0.75cm;
        }
        """)

        print(f"🚀 MlibDownloader 已初始化 | 默认根目录: {default_base_url or 'auto'}", flush=True)
        print(f"   采用磁盘二级缓存: {self._image_cache}", flush=True)

        # 【极致优化】：提前预缓存字体 CSS
        self._pre_cache_fonts()

    def _pre_cache_fonts(self):
        """提前将核心字体 CSS 拉入缓存，避免渲染时阻塞"""
        font_url = "https://cdn.jsdelivr.net/npm/@raineblog/mkdocs-fontkit@latest/dist/fonts.min.css"
        print(f"⏳ 正在预热字体缓存: {font_url}", flush=True)
        try:
            self._fetcher.fetch(font_url)
            print("   ✅ 字体缓存预热完成", flush=True)
        except Exception as e:
            print(f"   ⚠️ 字体预热失败 (不影响后续): {e}", flush=True)

    def add_task(self, task: List) -> None:
        """
        添加任务（支持多次调用）
        [html_source, pdf_path] 
        [html_source, pdf_path, base_url]   # 覆盖默认根目录
        """
        print(f'➕ 添加任务: {task}', flush=True)
        if len(task) == 2:
            html_source, pdf_path = task
            base_url = self.default_base_url
        elif len(task) == 3:
            html_source, pdf_path, base_url = task
        else:
            raise ValueError("task must be [html_source, pdf_path] or [html_source, pdf_path, base_url]")

        self._task_list.append((html_source, pdf_path, base_url))

    def start_tasks(self) -> None:
        """执行当前所有任务（单线程），执行完毕自动清空任务队列"""
        total = len(self._task_list)
        if total == 0:
            print("No tasks queued.", flush=True)
            return

        # 获取当前缓存状态
        stats = self.get_cache_stats()
        print(f"\n▶️ 新一批 {total} 个任务开始执行（极致缓存复用模式）", flush=True)
        print(f"   当前缓存：URL={stats['url_cache']} | 图片={stats['image_cache']}", flush=True)

        for i, (html_source, pdf_path_str, base_url) in enumerate(self._task_list, 1):
            pdf_path = pathlib.Path(pdf_path_str).expanduser().resolve()
            # 【实时日志】：确保每一行都即时刷新到终端
            print(f"[{i}/{total}] {html_source} → {pdf_path.name}  (base={base_url or 'auto'})", flush=True)

            try:
                pdf_path.parent.mkdir(parents=True, exist_ok=True)

                # 智能 base_url 处理
                src_path = pathlib.Path(html_source).expanduser()
                if base_url is not None:
                    effective_base = str(pathlib.Path(base_url).expanduser().resolve())
                elif src_path.is_file():
                    effective_base = str(src_path.parent.absolute())
                else:
                    effective_base = None

                # 【WeasyPrint 68.1 适配】：media_type 默认为 print
                if src_path.is_file():
                    html = HTML(
                        filename=str(src_path),
                        base_url=effective_base,
                        url_fetcher=self._fetcher,
                        media_type='print'
                    )
                else:
                    html = HTML(
                        url=html_source,
                        base_url=effective_base,
                        url_fetcher=self._fetcher,
                        media_type='print'
                    )

                html.write_pdf(
                    target=str(pdf_path),
                    stylesheets=[self._PAGE_CSS],
                    font_config=self._font_config,
                    # 【WeasyPrint 68.1 适配】：参数名改回了 cache，且支持硬盘路径字符串
                    cache=self._image_cache,
                    optimize_images=False,
                    uncompressed_pdf=True,
                    full_fonts=True,
                    hinting=True,
                    presentational_hints=True,
                )
                # 打印成功标记，立刻冲刷
                print(f"   ✅ 完成: {pdf_path.name}", flush=True)

            except Exception as e:
                print(f"   ❌ ERROR {html_source}: {type(e).__name__}: {e}", flush=True)

        print("🎉 本批任务全部完成！可通过 add_task 继续添加下一次批次。", flush=True)
        self._print_cache_stats()
        self._task_list.clear()   # 只清任务队列，缓存保留

    def _print_cache_stats(self) -> None:
        """打印当前缓存统计"""
        stats = self.get_cache_stats()
        print("📊 当前缓存统计:", flush=True)
        print(f"   • URL 缓存: {stats['url_cache']} 个资源 (CDN/字体等)", flush=True)
        print(f"   • 图片缓存: {stats['image_cache']} 个 (磁盘复用)", flush=True)
        print(f"   • 默认根目录: {self.default_base_url or 'auto'}", flush=True)

    def get_cache_stats(self) -> Dict[str, int]:
        """计算当前缓存数量"""
        try:
            # 统计磁盘临时目录里的图片文件数
            img_len = len(os.listdir(self._image_cache))
        except Exception:
            img_len = 0
            
        return {
            "url_cache": len(self._url_cache),
            "image_cache": img_len,
            "pending_tasks": len(self._task_list),
        }

    def clear_caches(self) -> None:
        """手动清空所有缓存"""
        self._url_cache.clear()
        # 清空磁盘目录
        try:
            for f in os.listdir(self._image_cache):
                os.remove(os.path.join(self._image_cache, f))
        except Exception:
            pass
        print("🧹 所有永久缓存已手动清空", flush=True)

    def __del__(self):
        """销毁时清理临时目录"""
        if hasattr(self, '_url_cache'):
            # 这里不用 print，因为程序退出时打印可能出问题，
            # 但如果一定要打印，确保 flush
            try:
                print("\n🗑️  MlibDownloader 任务销毁...", flush=True)
            except Exception:
                pass
        
        # 强制清理临时目录
        if hasattr(self, '_image_cache_dir'):
            try:
                self._image_cache_dir.cleanup()
            except Exception:
                pass


if __name__ == "__main__":
    print("=== MlibDownloader 多次复用示例 ===")