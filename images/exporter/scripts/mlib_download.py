# mlib_download.py
# WeasyPrint HTML-to-PDF 下载器 - 极致性能多线程版本
# 支持：无限次复用 + 永久缓存 + 自动适应多核/弱机 + 线程安全

import os
import gc
import pathlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections.abc import MutableMapping
from typing import Any, Dict, List, Optional, Tuple

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from weasyprint.urls import URLFetcher, URLFetcherResponse


class ThreadSafeCache(MutableMapping):
    """线程安全的缓存字典（用于多线程环境下的图片等内部缓存）"""

    def __init__(self):
        self.store = dict()
        self.lock = threading.Lock()

    def __getitem__(self, key):
        return self.store[
            key
        ]  # 字典读取在 Python (GIL) 中是原子的，无需加锁，最大化速度

    def __setitem__(self, key, value):
        with self.lock:
            self.store[key] = value

    def __delitem__(self, key):
        with self.lock:
            del self.store[key]

    def __iter__(self):
        with self.lock:
            return iter(list(self.store.keys()))

    def __len__(self):
        return len(self.store)

    def clear(self):
        with self.lock:
            self.store.clear()


class CachedURLFetcher(URLFetcher):
    """支持多线程双重检查锁定的内部缓存 fetcher，绝对防止并发重复下载"""

    def __init__(
        self, cache: MutableMapping[str, URLFetcherResponse], is_multithread: bool
    ):
        super().__init__()
        self.cache = cache
        self.is_multithread = is_multithread
        self.lock = threading.Lock() if is_multithread else None

    def fetch(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> URLFetcherResponse:
        # 极速路径（无需锁）
        if url in self.cache:
            return self.cache[url]

        if not self.is_multithread:
            response: URLFetcherResponse = super().fetch(url, headers=headers)
            self.cache[url] = response
            return response

        # 多线程下的双重检查锁定 (Double-checked locking)
        with self.lock:
            if url in self.cache:
                return self.cache[url]
            # 如果缓存真没有，才发起真实网络请求
            response: URLFetcherResponse = super().fetch(url, headers=headers)
            self.cache[url] = response
            return response


class MlibDownloader:
    """
    WeasyPrint 极限多线程下载器
    - 根据 MAX_THREADS 自动切换引擎 (单核降级无锁模式 / 多核高并发模式 / 16核+狂暴模式)
    """

    def __init__(self, default_base_url: Optional[str] = None):
        self.default_base_url = default_base_url
        self._task_list: List[Tuple[str, str, Optional[str]]] = []

        # 确定线程数
        env_threads = os.environ.get("MAX_THREADS")
        if env_threads and env_threads.isdigit():
            self.max_threads = int(env_threads)
        else:
            # 默认：Github Action 为 2，我们默认稍微超额使用 I/O 线程以加快网络速度
            self.max_threads = min(32, (os.cpu_count() or 1) * 2)

        self.is_multithread = self.max_threads > 1

        # 根据是否单线程，选择最佳缓存结构 (单线程避开锁开销)
        if self.is_multithread:
            self._image_cache = ThreadSafeCache()
            self._url_cache = ThreadSafeCache()
        else:
            self._image_cache: Dict[str, Any] = {}
            self._url_cache: Dict[str, URLFetcherResponse] = {}

        self._fetcher = CachedURLFetcher(self._url_cache, self.is_multithread)

        # 线程本地存储 (Thread-Local Storage)
        # WeasyPrint 的 FontConfiguration 在 C 层级非线程安全，必须每个线程持有一个独立实例
        self._thread_local = threading.local()

        # 单线程模式下可直接共享
        if not self.is_multithread:
            self._single_font_config = FontConfiguration()

        self._PAGE_CSS = CSS(
            string="""
        @page {
            size: A4 portrait;
            margin-top: 1cm; margin-bottom: 1cm;
            margin-left: 0.75cm; margin-right: 0.75cm;
        }
        """
        )

        # 终端输出防穿插锁
        self._print_lock = threading.Lock()

        self._safe_print(
            f"🚀 MlibDownloader 初始化 | 默认根目录: {default_base_url or 'auto'}"
        )
        if self.max_threads == 1:
            self._safe_print("   ⚡ 触发【单线程特殊优化】: 无锁结构，最高效利用单核。")
        elif self.max_threads >= 16:
            self._safe_print(
                f"   🔥 触发【高端主机狂暴模式】(Threads: {self.max_threads}): 开启并行，自动管理 GC 回收，牺牲硬盘换取极速 CPU。"
            )
        else:
            self._safe_print(
                f"   🌊 触发【常规多线程模式】(Threads: {self.max_threads}): 适应常规环境及 GitHub Actions。"
            )

    def _safe_print(self, *args, **kwargs):
        """线程安全的 print，防止多线程下终端字符错乱"""
        if self.is_multithread:
            with self._print_lock:
                print(*args, **kwargs)
        else:
            print(*args, **kwargs)

    def _get_font_config(self) -> FontConfiguration:
        """获取当前线程专属的 FontConfiguration"""
        if not self.is_multithread:
            return self._single_font_config

        if not hasattr(self._thread_local, "font_config"):
            self._thread_local.font_config = FontConfiguration()
        return self._thread_local.font_config

    def add_task(self, task: List) -> None:
        """添加任务 [html_source, pdf_path, (可选)base_url]"""
        if len(task) == 2:
            html_source, pdf_path = task
            base_url = self.default_base_url
        elif len(task) == 3:
            html_source, pdf_path, base_url = task
        else:
            raise ValueError(
                "任务必须是 [html_source, pdf_path] 或 [html_source, pdf_path, base_url]"
            )
        self._task_list.append((html_source, pdf_path, base_url))

    def _process_single_task(
        self,
        html_source: str,
        pdf_path_str: str,
        base_url: Optional[str],
        index: int,
        total: int,
    ):
        """核心处理逻辑（供线程池调用）"""
        try:
            pdf_path = pathlib.Path(pdf_path_str).expanduser().resolve()
            pdf_path.parent.mkdir(parents=True, exist_ok=True)

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
                    url=html_source, base_url=effective_base, url_fetcher=self._fetcher
                )

            # 获取线程专属 FontConfiguration
            font_config = self._get_font_config()

            # 高端主机优化：牺牲一定生成的 PDF 硬盘大小，最大化减少 CPU 计算时间
            is_high_end = self.max_threads >= 16

            html.write_pdf(
                target=str(pdf_path),
                stylesheets=[self._PAGE_CSS],
                font_config=font_config,
                cache=self._image_cache,  # 完全共享缓存池
                optimize_images=not is_high_end,  # 高端主机不优化图片，省 CPU 时间
                uncompressed_pdf=is_high_end,  # 高端主机不压缩 PDF，省 CPU 时间
                full_fonts=True,
                hinting=True,
                presentational_hints=True,
            )
            self._safe_print(f"   ✅ [{index}/{total}] 完成: {pdf_path.name}")
            return True
        except Exception as e:
            self._safe_print(
                f"   ❌ ERROR [{index}/{total}] {html_source}: {type(e).__name__}: {e}"
            )
            return False

    def start_tasks(self) -> None:
        """执行当前所有任务，执行完毕自动清空任务队列"""
        total = len(self._task_list)
        if total == 0:
            self._safe_print("任务队列为空。")
            return

        self._safe_print(f"\n▶️ 新批次 {total} 个任务开始执行")
        self._safe_print(
            f"   当前共享缓存池：URL={len(self._url_cache)} | 图片={len(self._image_cache)}"
        )

        # 【高端主机特殊优化】：如果有超多核心和大内存，关闭GC避免卡顿，加速DOM处理
        if self.max_threads >= 16 and gc.isenabled():
            gc.disable()
            self._safe_print(
                "   [高端主机优化] 已临时禁用垃圾回收 (GC) 以获取极限吞吐量..."
            )

        if self.max_threads == 1:
            # 单线程模式下同步执行
            for i, (html_source, pdf_path_str, base_url) in enumerate(
                self._task_list, 1
            ):
                self._process_single_task(html_source, pdf_path_str, base_url, i, total)
        else:
            # 多线程并发执行
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = []
                for i, (html_source, pdf_path_str, base_url) in enumerate(
                    self._task_list, 1
                ):
                    futures.append(
                        executor.submit(
                            self._process_single_task,
                            html_source,
                            pdf_path_str,
                            base_url,
                            i,
                            total,
                        )
                    )

                # 等待所有任务完成
                for future in as_completed(futures):
                    future.result()  # 捕捉未处理异常

        # 【高端主机特殊优化】：恢复 GC 并进行一次集中回收
        if self.max_threads >= 16:
            gc.enable()
            gc.collect()
            self._safe_print("   [高端主机优化] 本批次完成，GC 清理完毕。")

        self._safe_print("🎉 本批任务全部完成！队列已清空。")
        self._print_cache_stats()
        self._task_list.clear()

    def _print_cache_stats(self) -> None:
        stats = self.get_cache_stats()
        self._safe_print("📊 当前缓存统计:")
        self._safe_print(
            f"   • URL 缓存: {stats['url_cache']} 个资源 (已省去重复网络请求)"
        )
        self._safe_print(f"   • 图片缓存: {stats['image_cache']} 个 (内部解析共享)")
        self._safe_print(
            f"   • 线程模式: {'单线程极限优化' if self.max_threads == 1 else f'{self.max_threads} 线程池并发'}"
        )

    def get_cache_stats(self) -> Dict[str, int]:
        return {
            "url_cache": len(self._url_cache),
            "image_cache": len(self._image_cache),
            "pending_tasks": len(self._task_list),
        }

    def clear_caches(self) -> None:
        self._url_cache.clear()
        self._image_cache.clear()
        self._safe_print("🧹 所有永久缓存已手动清空")

    def __del__(self):
        if hasattr(self, "_url_cache") and hasattr(self, "_image_cache"):
            self._safe_print("\n🗑️  MlibDownloader 销毁进程...")
            self._print_cache_stats()


if __name__ == "__main__":
    print("=== MlibDownloader 极限并发版 测试 ===")

    # 你可以通过修改环境变量来测试不同的环境策略：
    # os.environ["MAX_THREADS"] = "1"   # 弱机单核模式测试
    # os.environ["MAX_THREADS"] = "16"  # 高端主机狂暴模式测试
    # os.environ["MAX_THREADS"] = "4"   # 正常并行测试

    downloader = MlibDownloader()

    # 模拟添加任务（注意，实际使用请替换为存在的有效 URL/文件）
    # downloader.add_task(["https://example.com", "example_1.pdf"])
    # downloader.add_task(["https://example.com", "example_2.pdf"]) # 这个会命中几乎 100% 缓存

    # downloader.start_tasks()
