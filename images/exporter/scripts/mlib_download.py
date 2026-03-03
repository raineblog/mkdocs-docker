import logging
import json
import sys
from typing import List, Dict

# ==========================================
# 运维友好型日志配置
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

class MlibDownloader:
    def __init__(self):
        logger.info("Initializing MlibDownloader Task Collector...")
        self._task_queue: List[Dict[str, str]] = []

    def add_task(self, html_source: str, pdf_path: str) -> None:
        self._task_queue.append({
            "url": html_source,
            "pdf_path": pdf_path
        })
        logger.debug(f"Queued task: {html_source} -> {pdf_path}")

    def save_tasks(self, output_json_path: str) -> None:
        total_tasks = len(self._task_queue)
        if not total_tasks:
            logger.warning("No tasks in the queue.")
            
        logger.info(f"Saving {total_tasks} PDF conversion tasks to {output_json_path}...")
        
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(self._task_queue, f, ensure_ascii=False, indent=4)
            
        logger.info("Tasks successfully saved.")
        self._task_queue.clear()


if __name__ == "__main__":
    pass
