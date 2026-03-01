# mlib_download.py
# WeasyPrint HTML-to-PDF 下载器 - Class 版本（支持无限次复用 + 永久缓存）
# 新增：多次复用支持（add_task → start_tasks → 继续 add_task → start_tasks...）
# 缓存（URL/图片/字体）跨批次永久保留，任务队列每次执行后自动清空

# import os
# import gc
import time
# import tempfile
import pathlib
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
    """内部缓存 fetcher（每个实例独立，但跨批次持久）"""

    def __init__(self, cache: MutableMapping[str, URLFetcherResponse]):
        super().__init__()
        self.cache = cache

    def get_total_size(self) -> int:
        """获取当前缓存的总字节数 (兼容多种响应对象类型)"""
        total = 0
        for resp in self.cache.values():
            try:
                # 优先作为字典处理
                if isinstance(resp, dict):
                    s = resp.get("string")
                else:
                    # 尝试作为对象属性处理
                    s = getattr(resp, "string", None)

                if s and isinstance(s, (bytes, str)):
                    total += len(s)
            except Exception:
                pass
        return total

    def fetch(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> URLFetcherResponse:
        # 极速命中路径
        if url in self.cache:
            resp = self.cache[url]
            return resp.copy() if isinstance(resp, dict) else resp

        # 发起真实获取
        try:
            response: URLFetcherResponse = super().fetch(url, headers=headers)
        except Exception as e:
            if not url.startswith(("http://", "https://")):
                print(f"\n   ⚠️ 资源加载异常 [{url}]: {e}", flush=True)
            raise e

        # 统一转为字典并处理 file_obj 泄露/关闭问题
        if response is not None:
            # 如果是本地资源且 fetcher 返回空或异常（WeasyPrint 某些版本 fallback 行为）
            # 我们在这里做一个安全的探测
            has_file_obj = False
            has_string = False

            if isinstance(response, dict):
                has_file_obj = "file_obj" in response
                has_string = "string" in response
            else:
                has_file_obj = hasattr(response, "file_obj")
                has_string = hasattr(response, "string")

            if has_file_obj and not has_string:
                try:
                    # 读取全部内容到内存，彻底解决 I/O closed 错误
                    f = (
                        response["file_obj"]
                        if isinstance(response, dict)
                        else response.file_obj
                    )
                    content = f.read()

                    if isinstance(response, dict):
                        response["string"] = content
                        del response["file_obj"]
                    else:
                        response = dict(response)
                        response["string"] = content
                        if "file_obj" in response:
                            del response["file_obj"]

                    try:
                        f.close()
                    except Exception:
                        pass
                except Exception:
                    pass

        self.cache[url] = response
        return response.copy() if isinstance(response, dict) else response


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

        # 【跨文档永久缓存】：使用字典而不是路径，确保持久化命中。
        # 在 68.1+ 中，cache 参数如果是 dict，则为内存常驻。
        self._image_cache: Dict[str, Any] = {}
        self._url_cache: Dict[str, URLFetcherResponse] = {}

        self._font_config = FontConfiguration()
        self._fetcher = CachedURLFetcher(self._url_cache)

        self._PAGE_CSS = CSS(
            string="""
        @page {
            size: A4 portrait;
            margin-top: 1cm;
            margin-bottom: 1cm;
            margin-left: 0.75cm;
            margin-right: 0.75cm;
        }
        """
        )

        print(
            f"🚀 MlibDownloader 已初始化 | 默认根目录: {default_base_url or 'auto'}",
            flush=True,
        )
        print("   引擎策略: 单线程极致缓存复用 (Memory-Resident Cache)", flush=True)

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
        print(f"➕ 添加任务: {task}", flush=True)
        if len(task) == 2:
            html_source, pdf_path = task
            base_url = self.default_base_url
        elif len(task) == 3:
            html_source, pdf_path, base_url = task
        else:
            raise ValueError(
                "task must be [html_source, pdf_path] or [html_source, pdf_path, base_url]"
            )

        self._task_list.append((html_source, pdf_path, base_url))

    def start_tasks(self) -> None:
        """执行当前所有任务（单线程），充分利用字典缓存池"""
        total = len(self._task_list)
        if total == 0:
            print("No tasks queued.", flush=True)
            return

        batch_start_time = time.time()

        # 获取初始缓存状态
        stats = self.get_cache_stats()
        print(
            f"\n▶️ 开始导出 {total} 个 PDF (已缓存: {stats['url_cache']} 项 / {stats['url_size_str']})",
            flush=True,
        )

        for i, (html_source, pdf_path_str, base_url) in enumerate(self._task_list, 1):
            task_start_time = time.time()
            pdf_path = pathlib.Path(pdf_path_str).expanduser().resolve()

            # 简化：一行输出进度，最后更新耗时与状态
            progress_prefix = f"[{i}/{total}] "
            print(f"{progress_prefix}正在处理: {pdf_path.name}...", end="", flush=True)

            try:
                pdf_path.parent.mkdir(parents=True, exist_ok=True)

                # 构造 HTML 对象
                src_path = pathlib.Path(html_source).expanduser()

                # 【关键修复】：base_url 必须是绝对路径的文件协议 URI (file:///)
                # 这能确保 WeasyPrint 正确处理 ../../../ 这种相对寻址
                if src_path.is_file():
                    effective_base = src_path.parent.resolve().as_uri()
                elif base_url:
                    effective_base = pathlib.Path(base_url).resolve().as_uri()
                else:
                    effective_base = None

                html_kwargs = {
                    "base_url": effective_base,
                    "url_fetcher": self._fetcher,
                    "media_type": "print",
                }
                if src_path.is_file():
                    html = HTML(filename=str(src_path), **html_kwargs)
                else:
                    html = HTML(url=html_source, **html_kwargs)

                # 执行渲染 - 极致性能配置
                html.write_pdf(
                    target=str(pdf_path),
                    stylesheets=[self._PAGE_CSS],
                    font_config=self._font_config,
                    cache=self._image_cache,
                    optimize_images=False,
                    uncompressed_pdf=False,  # 开启压缩，减少 IO 写入压力
                    full_fonts=False,  # 【核心优化】：使用字体子集化，极大提升速度
                    hinting=True,
                    presentational_hints=True,
                )

                duration = time.time() - task_start_time
                # 回写完成状态
                print(
                    f"\r{progress_prefix}✅ {pdf_path.name} ({duration:.2f}s) | 缓存={self.get_cache_stats()['url_size_str']}",
                    flush=True,
                )

            except Exception as e:
                print(f"\r{progress_prefix}❌ ERROR {pdf_path.name}: {e}", flush=True)

        batch_duration = time.time() - batch_start_time
        print(f"\n🎉 导出完成 | 总耗时: {batch_duration:.2f}s", flush=True)
        self._print_cache_stats()
        self._task_list.clear()

    def _print_cache_stats(self) -> None:
        """打印当前缓存统计"""
        stats = self.get_cache_stats()
        print("📊 缓存资源分布 (字节级分析):", flush=True)
        print(
            f"   • 网络层缓存 (CDN/字体): {stats['url_cache']} 项 | 总计: {stats['url_size_str']}",
            flush=True,
        )
        print(f"   • 页面图层缓存 (@media): {stats['image_cache']} 项", flush=True)
        print(f"   • 缓存策略: 跨文档内存常驻 (Max-Performance Mode)", flush=True)

    def get_cache_stats(self) -> Dict[str, Any]:
        """计算详细缓存指标"""
        url_size = self._fetcher.get_total_size()
        return {
            "url_cache": len(self._url_cache),
            "url_size_raw": url_size,
            "url_size_str": format_size(url_size),
            "image_cache": len(self._image_cache),
            "pending_tasks": len(self._task_list),
        }

    def clear_caches(self) -> None:
        """手动清空所有缓存"""
        self._url_cache.clear()
        self._image_cache.clear()
        print("🧹 所有永久缓存已从内存清除", flush=True)

    def __del__(self):
        """销毁时输出统计数据"""
        if hasattr(self, "_url_cache"):
            try:
                print("\n🗑️  MlibDownloader 实例生命周期结束", flush=True)
                self._print_cache_stats()
            except Exception:
                pass


if __name__ == "__main__":
    print("=== MlibDownloader 多次复用示例 ===")
