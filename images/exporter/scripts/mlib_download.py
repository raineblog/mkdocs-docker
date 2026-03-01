# mlib_download.py
# WeasyPrint HTML-to-PDF 下载器 - 极致性能与现代架构版 (V7)
# 针对 WeasyPrint 68.1+ 深度优化，解决 I/O 冲突、路径寻址与缓存漏记问题

import io
import re
import time
import pathlib
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple, MutableMapping
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from weasyprint.urls import URLFetcher, URLFetcherResponse


def format_size(size_bytes: int) -> str:
    """格式化字节数为人类可读格式"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


class CachedURLFetcher(URLFetcher):
    """
    高度隔离的现代缓存 Fetcher
    - 支持 WeasyPrint 68.1+ 的 URLFetcherResponse 规范
    - 内存中仅存储原始 bytes，每次请求返回全新的 BytesIO 实例以避免 I/O 冲突
    """

    def __init__(self, cache_pool: MutableMapping[str, Dict[str, Any]]):
        super().__init__()
        self.cache_pool = cache_pool

    def get_total_size(self) -> int:
        """准确计算缓存中所有资源的字节总数"""
        return sum(len(item["content"]) for item in self.cache_pool.values() if "content" in item)

    def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> URLFetcherResponse:
        # 1. 缓存快照命中
        if url in self.cache_pool:
            c = self.cache_pool[url]
            return URLFetcherResponse(
                url=c.get("url", url),
                body=io.BytesIO(c["content"]),
                mime_type=c.get("mime_type"),
                encoding=c.get("encoding"),
                redirected_url=c.get("redirected_url")
            )

        # 1.5. 路径补全修正 (针对由于 HTML 中的绝对路径导致解析到根目录的情况)
        if url.startswith("file://") and "/site/" not in url:
            # 尝试在当前工作目录的 site 下寻找
            # urllib.parse 可能将 href="/assets/..." 解析成了 file:///assets/...
            # 还原为类似 file:///app/site/assets/...
            parsed = urllib.parse.urlparse(url)
            local_path = urllib.request.url2pathname(parsed.path)
            # 剥离多余的前缀（如 /__w/assets 或 /assets）并映射到 ./site
            # 这里做个简单的 heuristic: 如果原先找不着，强制映射到 ./site/...
            import os
            
            path_parts = pathlib.Path(local_path).parts
            for i in range(len(path_parts)):
                # Strip leading root separators (e.g. '/' or 'C:\')
                if path_parts[i] in ['/', '\\'] or path_parts[i].endswith(':\\'):
                    continue
                rel_path = os.path.join(*path_parts[i:])
                potential_path = os.path.abspath(os.path.join("site", rel_path))
                if os.path.exists(potential_path):
                    url = pathlib.Path(potential_path).as_uri()
                    break


        # 2. 发起真实获取
        try:
            # 调用基类 fetch
            response = super().fetch(url, headers=headers)
        except Exception as e:
            # 记录资产加载失败（屏蔽网络类静默失败，重点关注本地资源）
            if not url.startswith(("http://", "https://")):
                print(f"\n   ⚠️ 资源获取失败 [{url}]: {e}", flush=True)
            raise e

        # 3. 内容解构与持久化入库
        if response is not None:
            try:
                # 兼容旧版 dict 返回和新版对象返回
                is_dict = isinstance(response, dict)
                
                # 探测内容 (body 是现代规范的首选字段)
                raw_body = response.get("string") or response.get("file_obj") if is_dict else \
                           getattr(response, "body", None) or getattr(response, "string", None) or getattr(response, "file_obj", None)

                content: Optional[bytes] = None
                if isinstance(raw_body, (bytes, str)):
                    content = raw_body if isinstance(raw_body, bytes) else raw_body.encode("utf-8")
                elif hasattr(raw_body, "read"):
                    content = raw_body.read()
                    try:
                        raw_body.close()
                    except Exception:
                        pass
                
                if content is not None:
                    # 提取元数据
                    meta = {
                        "content": content,
                        "url": response.get("url", url) if is_dict else getattr(response, "url", url),
                        "mime_type": response.get("mime_type") if is_dict else getattr(response, "mime_type", None),
                        "encoding": response.get("encoding") if is_dict else getattr(response, "encoding", None),
                        "redirected_url": response.get("redirected_url") if is_dict else getattr(response, "redirected_url", None)
                    }
                    self.cache_pool[url] = meta
                    
                    # 返回全新的独占流
                    return URLFetcherResponse(
                        url=meta["url"],
                        body=io.BytesIO(content),
                        mime_type=meta["mime_type"],
                        encoding=meta["encoding"],
                        redirected_url=meta["redirected_url"]
                    )
            except Exception as e:
                # 如果解构失败，至少返回原始响应
                pass

        return response


class MlibDownloader:
    """
    PDF 下载器核心类 (V7 Refactored)
    - 职责：任务调度、共享缓存管理、PDF 引擎控制
    """

    def __init__(self, default_base_url: Optional[str] = None):
        self.default_base_url = default_base_url
        self._task_queue: List[Tuple[str, str, Optional[str]]] = []
        
        # 共享资源池
        self._url_cache_pool: Dict[str, Dict[str, Any]] = {}
        self._image_rendering_cache: Dict[str, Any] = {}
        
        # 引擎配置单例化
        self._font_config = FontConfiguration()
        self._fetcher = CachedURLFetcher(self._url_cache_pool)

        # 预设页面样式
        self._page_css = CSS(string="@page { size: A4; margin: 1cm 0.75cm; }")

        print(f"🚀 MlibDownloader V7 初始化 | 根目录: {default_base_url or 'auto'}", flush=True)
        
        # 预热核心资产 (可选)
        font_kit = "https://cdn.jsdelivr.net/npm/@raineblog/mkdocs-fontkit@latest/dist/fonts.min.css"
        self._warm_up_resource(font_kit)

    def _warm_up_resource(self, url: str) -> None:
        """预热资源并尝试爬取关联字体"""
        try:
            print(f"⏳ 正在预热核心资产: {url}", flush=True)
            resp = self._fetcher.fetch(url)
            
            # 进阶优化：如果是 CSS，尝试预测并预加载里面的字体文件以平摊首个 PDF 的加载压力
            if resp and "font-face" in url.lower() or ".css" in url.lower():
                try:
                    content = self._url_cache_pool.get(url, {}).get("content", b"").decode("utf-8", errors="ignore")
                    font_urls = re.findall(r'url\((["\']?)(.*?)\1\)', content)
                    if font_urls:
                        print(f"   ⚓ 探测到 {len(font_urls)} 个关联字体资源，正在并行预载...", flush=True)
                        for _, f_url in font_urls:
                            if f_url.startswith(("http", "//")):
                                full_url = f_url if f_url.startswith("http") else "https:" + f_url
                                try:
                                    self._fetcher.fetch(full_url)
                                except Exception: pass
                except Exception: pass
            
            print(f"   ✅ 资产预热完成 (当前缓存: {format_size(self._fetcher.get_total_size())})", flush=True)
        except Exception as e:
            print(f"   ⚠️ 资产预热跳过: {e}", flush=True)

    def add_task(self, html_source: str, pdf_path: str, base_url: Optional[str] = None) -> None:
        """添加待处理任务"""
        print(f"➕ 添加任务: {pathlib.Path(pdf_path).name}", flush=True)
        self._task_queue.append((html_source, pdf_path, base_url or self.default_base_url))

    def start_tasks(self) -> None:
        """执行队列中的所有任务"""
        if not self._task_queue:
            return

        batch_start = time.time()
        total = len(self._task_queue)
        print(f"\n▶️ 开始生产 {total} 份 PDF | 初始缓存: {format_size(self._fetcher.get_total_size())}", flush=True)

        for i, (src, dst, base) in enumerate(self._task_queue, 1):
            task_start = time.time()
            dst_path = pathlib.Path(dst).resolve()
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            prefix = f"[{i}/{total}] "
            print(f"{prefix}正在渲染: {dst_path.name}...", end="", flush=True)

            try:
                # 路径标准化
                src_p = pathlib.Path(src).expanduser()
                eff_base = None
                if base:
                    eff_base = pathlib.Path(base).resolve().as_uri()
                    if not eff_base.endswith("/"): eff_base += "/"
                elif src_p.is_file():
                    eff_base = src_p.parent.resolve().as_uri() + "/"

                # 实例化 HTML 对象
                html_kwargs = {"base_url": eff_base, "url_fetcher": self._fetcher, "media_type": "print"}
                html = HTML(filename=str(src_p), **html_kwargs) if src_p.is_file() else HTML(url=src, **html_kwargs)

                # 渲染导出
                html.write_pdf(
                    target=str(dst_path),
                    stylesheets=[self._page_css],
                    font_config=self._font_config,
                    cache=self._image_rendering_cache,
                    full_fonts=False, # 极致性能的关键：字体子集化
                    optimize_images=False,
                    uncompressed_pdf=False,
                    hinting=True,
                    presentational_hints=True
                )

                elapsed = time.time() - task_start
                status = f"✅ {dst_path.name} ({elapsed:.2f}s) | 累计缓存={format_size(self._fetcher.get_total_size())}"
                print(f"\r{prefix}{status}", flush=True)

            except Exception as e:
                print(f"\r{prefix}❌ 失败 {dst_path.name}: {e}", flush=True)

        print(f"\n🎉 批次任务完成 | 总耗时: {time.time() - batch_start:.2f}s", flush=True)
        self._task_queue.clear()
        self._report_stats()

    def _report_stats(self) -> None:
        """输出详细审计报告"""
        size = self._fetcher.get_total_size()
        print("📊 资源审计报告 (Shared Global Pool):", flush=True)
        print(f"   • 全局 fetcher 缓存: {len(self._url_cache_pool)} 项 | 大小: {format_size(size)}", flush=True)
        print(f"   • 图片对象缓存池: {len(self._image_rendering_cache)} 项", flush=True)
        print(f"   • 缓存持久化策略: 内存常驻 + BytesIO 隔离", flush=True)

    def __del__(self):
        # 优雅清理
        if hasattr(self, "_url_cache_pool") and self._url_cache_pool:
            print("\n🗑️  MlibDownloader 实例生命周期结束", flush=True)
            self._report_stats()


if __name__ == "__main__":
    print("=== MlibDownloader V7 Multi-Process Entry Point ===")
