import logging
import pathlib
import hashlib
import json
import sys
from typing import Any, Dict, List, Optional, Tuple, MutableMapping

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from weasyprint.urls import URLFetcher, URLFetcherResponse

# ==========================================
# 运维友好型日志配置
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s[%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S ",
    stream=sys.stdout,  # CI 环境推荐统一输出到 stdout
)

logger = logging.getLogger(__name__)

# [运维贴士]：WeasyPrint 和字体解析库默认会输出大量的 CSS 不支持警告。
# 在 CI 环境中通常只需关心 Error，这里将其静音以避免日志被无用警告刷屏。
logging.getLogger("weasyprint").setLevel(logging.ERROR)
logging.getLogger("fontTools").setLevel(logging.ERROR)

# [修改核心 2] 继承官方的 URLFetcher
class DiskCacheFetcher(URLFetcher):
    def __init__(self, cache_dir: str | pathlib.Path, **kwargs):
        # 必须初始化父类，WeasyPrint 会在底层借此初始化 SSL 和超时配置
        super().__init__(**kwargs)
        
        self.cache_dir = pathlib.Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.url_to_path: dict[str, pathlib.Path] = {}
        self.url_to_mime: dict[str, str] = {}
        self.index_file = self.cache_dir / "cache_index.json"
        self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for url, info in data.items():
                        self.url_to_path[url] = pathlib.Path(info['path'])
                        self.url_to_mime[url] = info['mime_type']
            except Exception as e:
                logger.error(f"[Cache Load Error] {e}")

    def _save_index(self):
        data = {
            url: {
                'path': str(self.url_to_path[url].resolve()),
                'mime_type': self.url_to_mime[url]
            }
            for url in self.url_to_path
        }
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    # [修改核心 3] 方法签名增加 headers=None 以兼容新版父类
    def fetch(self, url, headers=None):
        if not (url.startswith('http://') or url.startswith('https://')):
            #[修改核心 4] 不再使用 default_url_fetcher，而是调用父类方法
            return super().fetch(url, headers)
            
        # --- 1. 尝试命中缓存 ---
        if url in self.url_to_path:
            local_path = self.url_to_path[url]
            if local_path.exists():
                logger.debug(f"✅ [Cache Hit] {url} -> {local_path.name}")
                mime_type = self.url_to_mime.get(url, 'application/octet-stream')
                
                # [修改核心 5] 返回时必须构造 URLFetcherResponse 对象
                return URLFetcherResponse(
                    url=url,
                    body=local_path.read_bytes(),
                    headers={'Content-Type': mime_type}
                )
            else:
                del self.url_to_path[url]
                del self.url_to_mime[url]

        # --- 2. 未命中，发起真实网络请求 ---
        logger.debug(f"🌐[Downloading] {url} ...")
        # 这里返回的 result 是一个 URLFetcherResponse 实例
        result = super().fetch(url, headers)
        
        # [修改核心 6] 读取并处理 body 流
        if hasattr(result.body, 'read'):
            resource_bytes = result.body.read()
            # 【重要】读取流后必须把 bytes 写回，否则 WeasyPrint 后续拿到的会是空流
            result.body = resource_bytes
        elif isinstance(result.body, str):
            resource_bytes = result.body.encode('utf-8')
        else:
            resource_bytes = result.body

        # 获取 MIME type
        mime_type = 'application/octet-stream'
        if result.headers and 'Content-Type' in result.headers:
            # result.headers 是类字典对象，值可能长这样 "text/css; charset=utf-8"
            mime_type = str(result.headers['Content-Type']).split(';')[0].strip()

        # --- 3. 落盘并更新字典 ---
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        original_ext = pathlib.Path(url.split('?')[0]).suffix
        if not original_ext or len(original_ext) > 8:
            original_ext = ""
            
        local_filename = f"{url_hash}{original_ext}"
        local_path = self.cache_dir / local_filename
        
        local_path.write_bytes(resource_bytes)
        
        self.url_to_path[url] = local_path
        self.url_to_mime[url] = mime_type
        self._save_index()
        
        return result

class MlibDownloader:
    def __init__(self, default_cache_dir: str = "./.cache/weasyprint"):
        self._images_cache_dir = pathlib.Path(default_cache_dir).resolve() / 'images'
        self._remote_cache_dir = pathlib.Path(default_cache_dir).resolve() / 'remote'

        self._optimized_fetcher = DiskCacheFetcher(cache_dir=self._remote_cache_dir)

        self._task_queue: List[Tuple[str, str]] = []
        self._font_config = FontConfiguration()

        self._base_stylesheets = [
            CSS(
                string="@page { size: A4; margin: 1cm 0.75cm; }"
            ),
            CSS(
                url="https://cdn.jsdelivr.net/npm/@raineblog/mkdocs-fontkit@latest/dist/fonts.min.css",
                url_fetcher=self._optimized_fetcher,
                font_config=self._font_config
            ),
        ]

        logger.info("Initialized MlibDownloader")

    def add_task(self, html_source: str, pdf_path: str) -> None:
        self._task_queue.append((html_source, pdf_path))
        # 使用 DEBUG 级别记录添加队列动作，避免在 INFO 级别时过于啰嗦
        logger.debug(f"Queued task: {html_source} -> {pdf_path}")

    def start_tasks(self) -> None:
        total_tasks = len(self._task_queue)
        if not total_tasks:
            logger.warning("No tasks in the queue. Exiting.")
            return

        logger.info(f"[Starting PDF conversion batch: {total_tasks} files...]")

        for i, (src, dst) in enumerate(self._task_queue, 1):
            src_p = pathlib.Path(src).resolve()
            dst_p = pathlib.Path(dst).resolve()

            base_p = src_p.parent

            # CI 友好的进度条：使用 [1/10] 格式做前缀，线性追加日志
            progress_prefix = f"[{i}/{total_tasks}]"
            logger.info(f"{progress_prefix} Converting {src_p.name} -> {dst_p.name} ...")

            try:
                dst_p.parent.mkdir(parents=True, exist_ok=True)

                html = HTML(
                    filename=src_p,
                    base_url=base_p,
                    url_fetcher=self._optimized_fetcher,
                    media_type="print"
                )

                html.write_pdf(
                    target=dst_p,
                    stylesheets=self._base_stylesheets,
                    font_config=self._font_config,
                    cache=self._images_cache_dir,
                    full_fonts=False,
                    uncompressed_pdf=True,
                    presentational_hints=True,
                    optimize_images=False,
                )

            except Exception as e:
                # 记录详细的异常堆栈 (exc_info=True)
                logger.error(
                    f"[{progress_prefix}] Failed to convert {src_p.name}: {str(e)}",
                    exc_info=True,
                )
                # 运维关键：捕获记录后向上抛出，使脚本以退出码非 0 结束，阻断 CI 流程
                raise

        logger.info("[All tasks completed successfully.]")
        self._task_queue.clear()


if __name__ == "__main__":
    # 模拟测试用例
    # downloader = MlibDownloader()
    # downloader.add_task("site/index.html", "output/index.pdf")
    # downloader.start_tasks()
    pass
