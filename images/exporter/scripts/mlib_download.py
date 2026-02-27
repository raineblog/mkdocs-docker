# mlib_download.py
# WeasyPrint HTML-to-PDF 下载器 - Class 版本（支持无限次复用 + 永久缓存）
# 新增：多次复用支持（add_task → start_tasks → 继续 add_task → start_tasks...）
# 缓存（URL/图片/字体）跨批次永久保留，任务队列每次执行后自动清空

import pathlib
from collections.abc import MutableMapping
from typing import Any, Dict, List, Optional, Tuple

import weasyprint
from weasyprint import CSS, FontConfiguration, HTML
from weasyprint.urls import URLFetcher, URLFetcherResponse


class CachedURLFetcher(URLFetcher):
    """内部缓存 fetcher（每个实例独立，但跨批次持久）"""
    def __init__(self, cache: MutableMapping[str, URLFetcherResponse]):
        super().__init__()
        self.cache = cache

    def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> URLFetcherResponse:
        if url in self.cache:
            return self.cache[url]
        response: URLFetcherResponse = super().fetch(url, headers=headers)
        self.cache[url] = response
        return response


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

        # 实例级永久缓存（多次复用关键）
        self._image_cache: Dict[str, Any] = {}
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

        print(f"🚀 MlibDownloader 已初始化 | 默认根目录: {default_base_url or 'auto (文件父目录)'}")
        print("   支持无限次复用：缓存将永久保留，适合批量多次执行")

    def add_task(self, task: List) -> None:
        """
        添加任务（支持多次调用）
        [html_source, pdf_path] 
        [html_source, pdf_path, base_url]   # 覆盖默认根目录
        """
        print('➕ 添加任务', task)
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
            print("No tasks queued.")
            return

        # 复用模式日志（让你看到缓存效果）
        print(f"\n▶️ 新一批 {total} 个任务开始执行（复用模式）")
        print(f"   当前缓存：URL={len(self._url_cache)} | 图片={len(self._image_cache)}（跨批次复用）")

        for i, (html_source, pdf_path_str, base_url) in enumerate(self._task_list, 1):
            pdf_path = pathlib.Path(pdf_path_str).expanduser().resolve()
            print(f"[{i}/{total}] {html_source} → {pdf_path}  (base={base_url or 'auto'})")

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

                if src_path.is_file():
                    html = HTML(
                        filename=str(src_path),
                        base_url=effective_base,
                        url_fetcher=self._fetcher,
                    )
                else:
                    html = HTML(
                        url=html_source,
                        base_url=effective_base,
                        url_fetcher=self._fetcher,
                    )

                html.write_pdf(
                    target=str(pdf_path),
                    stylesheets=[self._PAGE_CSS],
                    font_config=self._font_config,
                    cache=self._image_cache,
                    optimize_images=False,
                    uncompressed_pdf=True,
                    full_fonts=True,
                    hinting=True,
                    presentational_hints=True,
                )

            except Exception as e:
                print(f"  ❌ ERROR {html_source}: {type(e).__name__}: {e}")

        print("✅ 本批任务全部完成！任务队列已清空，可继续添加下一批")
        self._print_cache_stats()
        self._task_list.clear()   # 只清任务队列，缓存保留

    def _print_cache_stats(self) -> None:
        """打印当前缓存统计"""
        stats = self.get_cache_stats()
        print("📊 当前缓存统计:")
        print(f"   • URL 缓存: {stats['url_cache']} 个资源（CDN/CSS/字体/图片永久复用）")
        print(f"   • 图片缓存: {stats['image_cache']} 个")
        print(f"   • 待处理任务: {stats['pending_tasks']} 个")
        print(f"   • 默认根目录: {self.default_base_url or 'auto'}")

    def get_cache_stats(self) -> Dict[str, int]:
        """手动获取缓存统计"""
        return {
            "url_cache": len(self._url_cache),
            "image_cache": len(self._image_cache),
            "pending_tasks": len(self._task_list),
        }

    def clear_caches(self) -> None:
        """可选：手动清空所有缓存（仅在需要完全重置时调用）"""
        self._url_cache.clear()
        self._image_cache.clear()
        print("🧹 所有缓存已手动清空")

    def __del__(self):
        """对象销毁时自动输出最终日志"""
        if hasattr(self, '_url_cache') and hasattr(self, '_image_cache'):
            print("\n🗑️  MlibDownloader 对象正在销毁（程序结束）...")
            self._print_cache_stats()
            print("   所有缓存已释放")


if __name__ == "__main__":
    print("=== MlibDownloader 多次复用示例 ===")
