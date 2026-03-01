import pathlib
from typing import Any, Dict, List, Optional, Tuple, MutableMapping

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# 引入 rich 相关的组件
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

class MlibDownloader:
    def __init__(self, default_base_url: str = "./site", default_cache_dir: str = "./.cache/weasyprint"):
        self.site_root = pathlib.Path(default_base_url).resolve()
        self.cache_dir = pathlib.Path(default_cache_dir).resolve()

        self._task_queue: List[Tuple[str, str]] = []

        self._base_stylesheets =[
            CSS(string="@page { size: A4; margin: 1cm 0.75cm; }"),
            CSS(url="https://cdn.jsdelivr.net/npm/@raineblog/mkdocs-fontkit@latest/dist/fonts.min.css")
        ]
        
        # 初始化 rich Console 用于日志输出
        self.console = Console()
        self.console.log(f"[bold green]MlibDownloader 初始化成功[/bold green]")
        self.console.log(f"Site Root: [cyan]{self.site_root}[/cyan]")
        self.console.log(f"Cache Dir: [cyan]{self.cache_dir}[/cyan]")

    def add_task(self, html_source: str, pdf_path: str) -> None:
        self._task_queue.append((html_source, pdf_path))
        # 任务添加时打印一条低调的日志
        self.console.print(f"[dim]已添加任务: {html_source} -> {pdf_path}[/dim]")

    def start_tasks(self) -> None:
        total_tasks = len(self._task_queue)
        if not total_tasks:
            self.console.log("[yellow]任务队列为空，没有需要处理的任务。[/yellow]")
            return

        self.console.log(f"[bold blue]开始处理 {total_tasks} 个 PDF 渲染任务...[/bold blue]")

        # 配置 rich 进度条的显示样式
        progress_columns = (
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            "•",
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
        )

        with Progress(*progress_columns, console=self.console) as progress:
            # 添加主进度条任务
            task_id = progress.add_task("[cyan]准备渲染...", total=total_tasks)

            for i, (src, dst) in enumerate(self._task_queue, 1):
                src_p = pathlib.Path(src).resolve()
                dst_p = pathlib.Path(dst).resolve()
                
                # 动态更新进度条的描述，显示当前正在处理的文件
                progress.update(task_id, description=f"[cyan]正在渲染 ({i}/{total_tasks}): {src_p.name}")

                dst_p.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    html = HTML(
                        filename=src_p,
                        base_url=str(self.site_root),
                        cache=self.cache_dir,
                        media_type="print"
                    )

                    html.write_pdf(
                        target=dst_p,
                        stylesheets=self._base_stylesheets,
                        cache=self.cache_dir,
                        full_fonts=False,
                        uncompressed_pdf=True,
                        presentational_hints=True,
                        optimize_images=False
                    )
                except Exception as e:
                    # 如果发生错误，直接在进度条上方打印错误日志，不中断后续任务
                    self.console.print(f"[bold red]渲染失败:[/bold red] {src_p.name} - {e}")

                # 完成当前文件，步进进度条
                progress.advance(task_id)

        self._task_queue.clear()
        self.console.log("[bold green]✨ 所有任务处理完毕！队列已清空。[/bold green]")


if __name__ == "__main__":
    # 测试用例：你可以直接运行本文件查看效果
    downloader = MlibDownloader()
    
    # 创建几个模拟的本地 HTML 文件用来展示进度条效果

    # dummy_html_dir = pathlib.Path("./dummy_html")
    # dummy_html_dir.mkdir(exist_ok=True)
    
    # for i in range(5):
    #     dummy_file = dummy_html_dir / f"test_page_{i}.html"
    #     dummy_file.write_text(f"<h1>Hello World {i}</h1>", encoding="utf-8")
    #     downloader.add_task(str(dummy_file), f"./output/test_page_{i}.pdf")
        
    # 开始执行
    # downloader.start_tasks()