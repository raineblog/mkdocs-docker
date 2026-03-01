import logging
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple, MutableMapping

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# ==========================================
# 运维友好型日志配置
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s[%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,  # CI 环境推荐统一输出到 stdout
)

logger = logging.getLogger(__name__)

# [运维贴士]：WeasyPrint 和字体解析库默认会输出大量的 CSS 不支持警告。
# 在 CI 环境中通常只需关心 Error，这里将其静音以避免日志被无用警告刷屏。
logging.getLogger("weasyprint").setLevel(logging.ERROR)
logging.getLogger("fontTools").setLevel(logging.ERROR)


class MlibDownloader:
    def __init__(
        self,
        default_base_url: str = "./site",
        default_cache_dir: str = "./.cache/weasyprint",
    ):
        self.site_root = pathlib.Path(default_base_url).resolve()
        self.cache_dir = pathlib.Path(default_cache_dir).resolve()

        self._task_queue: List[Tuple[str, str]] = []

        self._base_stylesheets = [
            CSS(string="@page { size: A4; margin: 1cm 0.75cm; }"),
            CSS(
                url="https://cdn.jsdelivr.net/npm/@raineblog/mkdocs-fontkit@latest/dist/fonts.min.css"
            ),
        ]

        logger.info(f"Initialized MlibDownloader (Base URL: {self.site_root})")

    def add_task(self, html_source: str, pdf_path: str) -> None:
        self._task_queue.append((html_source, pdf_path))
        # 使用 DEBUG 级别记录添加队列动作，避免在 INFO 级别时过于啰嗦
        logger.debug(f"Queued task: {html_source} -> {pdf_path}")

    def start_tasks(self) -> None:
        total_tasks = len(self._task_queue)
        if not total_tasks:
            logger.warning("No tasks in the queue. Exiting.")
            return

        logger.info(f"🚀 Starting PDF conversion batch: {total_tasks} files...")

        for i, (src, dst) in enumerate(self._task_queue, 1):
            src_p = pathlib.Path(src).resolve()
            dst_p = pathlib.Path(dst).resolve()

            # CI 友好的进度条：使用 [1/10] 格式做前缀，线性追加日志
            progress_prefix = f"[{i}/{total_tasks}]"
            logger.info(
                f"{progress_prefix} Converting {src_p.name} -> {dst_p.name} ..."
            )

            try:
                dst_p.parent.mkdir(parents=True, exist_ok=True)

                html = HTML(filename=src_p, base_url=self.site_root, media_type="print")

                html.write_pdf(
                    target=dst_p,
                    stylesheets=self._base_stylesheets,
                    cache=self.cache_dir,
                    full_fonts=False,
                    uncompressed_pdf=True,
                    presentational_hints=True,
                    optimize_images=False,
                )

            except Exception as e:
                # 记录详细的异常堆栈 (exc_info=True)
                logger.error(
                    f"{progress_prefix} ❌ Failed to convert {src_p.name}: {str(e)}",
                    exc_info=True,
                )
                # 运维关键：捕获记录后向上抛出，使脚本以退出码非 0 结束，阻断 CI 流程
                raise

        logger.info("✅ All tasks completed successfully.")
        self._task_queue.clear()


if __name__ == "__main__":
    # 模拟测试用例
    # downloader = MlibDownloader()
    # downloader.add_task("site/index.html", "output/index.pdf")
    # downloader.start_tasks()
    pass
