import logging
import pathlib
import hashlib
import json
import sys
from typing import Any, Dict, List, Optional, Tuple, MutableMapping

from weasyprint import HTML, CSS, default_url_fetcher
from weasyprint.text.fonts import FontConfiguration

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

class DiskCacheFetcher:
    def __init__(self, cache_dir: pathlib.Path):
        """
        初始化基于目录的缓存抓取器
        """
        self.cache_dir = cache_dir.resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 核心字典：映射 URL 到 pathlib.Path
        self.url_to_path: dict[str, pathlib.Path] = {}
        
        # 辅助字典：记录 URL 对应的 mime_type (WeasyPrint 强依赖 mime_type)
        self.url_to_mime: dict[str, str] = {}
        
        # 索引文件路径，用于持久化缓存映射（这样哪怕重启脚本，也能复用上次下载的资源）
        self.index_file = self.cache_dir / "cache_index.json"
        self._load_index()

        logger.info(f"Initialized Remote Cache ({self.cache_dir})")

    def _load_index(self):
        """从本地加载之前的映射记录"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for url, info in data.items():
                        # 还原为 pathlib.Path 对象
                        self.url_to_path[url] = pathlib.Path(info['path'])
                        self.url_to_mime[url] = info['mime_type']
            except Exception as e:
                logger.error(f"[Cache Load Error] {e}", exc_info=True)
                raise

    def _save_index(self):
        """将当前的映射记录保存到本地 JSON"""
        data = {
            url: {
                'path': str(self.url_to_path[url].resolve()), # 存储绝对路径字符串
                'mime_type': self.url_to_mime[url]
            }
            for url in self.url_to_path
        }
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def fetch(self, url):
        """
        WeasyPrint 将调用的抓取函数
        """
        # 1. 如果不是 http/https 请求（比如 data:, file://），直接放行交给默认抓取器
        if not (url.startswith('http://') or url.startswith('https://')):
            return default_url_fetcher(url)
            
        # 2. 检查是否命中本地目录缓存
        if url in self.url_to_path:
            local_path = self.url_to_path[url]
            if local_path.exists():
                # print(f"✅ [Cache Hit] {url} -> {local_path.name}")
                logger.debug(f"[Cache Hit] {url} -> {local_path.name}")
                return {
                    'string': local_path.read_bytes(),
                    'mime_type': self.url_to_mime[url]
                }
            else:
                # 文件丢失，从缓存字典中剔除
                del self.url_to_path[url]
                del self.url_to_mime[url]

        # 3. 未命中缓存，发起真实网络请求
        # print(f"🌐 [Downloading] {url} ...")
        logger.debug(f"[Downloading] {url} ...")
        # 使用默认抓取器获取资源（这会帮我们处理重定向、SSL 证书等网络细节）
        result = default_url_fetcher(url)
        
        # 获取资源字节和 MIME 类型
        # WeasyPrint 默认返回 dict，包含 'string' (或 'file_obj') 和 'mime_type'
        if 'string' in result:
            resource_bytes = result['string']
        elif 'file_obj' in result:
            resource_bytes = result['file_obj'].read()
            result['string'] = resource_bytes  # 转为 string 方便后续处理
        else:
            return result
            
        mime_type = result.get('mime_type', 'application/octet-stream')

        # 4. 生成安全的文件名并存入目录
        # 使用 URL 的 MD5 作为文件名，避免非法字符，同时截取后缀名方便调试观察
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        original_ext = pathlib.Path(url.split('?')[0]).suffix  # 忽略 URL 参数提取后缀
        if not original_ext or len(original_ext) > 8:
            original_ext = ""
            
        local_filename = f"{url_hash}{original_ext}"
        local_path = self.cache_dir / local_filename
        
        # 将文件落盘
        local_path.write_bytes(resource_bytes)
        
        # 5. 更新字典并持久化
        self.url_to_path[url] = local_path
        self.url_to_mime[url] = mime_type
        self._save_index()
        
        # 6. 返回 WeasyPrint 要求的字典格式
        return result

class MlibDownloader:
    def __init__(self, default_cache_dir: str = "./.cache/weasyprint"):
        self._images_cache_dir = pathlib.Path(default_cache_dir).resolve() / 'images'
        self._remote_cache_dir = pathlib.Path(default_cache_dir).resolve() / 'remote'

        self._cache_manager = DiskCacheFetcher(cache_dir=self._remote_cache_dir)
        self._optimized_fetcher = self._cache_manager.fetch

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
