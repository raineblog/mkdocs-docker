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
from weasyprint.urls import URLFetcher, URLFetcherResponse, default_url_fetcher


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
    极致性能与路径兼容的现代 Fetcher (V8)
    - 支持 WeasyPrint 68.1+ 规范
    - 智能路径重定向：将绝对路径、Github Runner 路径自动映射到 site 目录
    - 共享内存缓存：多任务间共享资源，避免重复 fetch
    """

    def __init__(
        self, cache_pool: MutableMapping[str, Dict[str, Any]], site_root: pathlib.Path
    ):
        super().__init__()
        self.cache_pool = cache_pool
        self.site_root = site_root.resolve()

    def get_total_size(self) -> int:
        return sum(len(item["content"]) for item in self.cache_pool.values() if "content" in item)

    def _resolve_local_url(self, url: str) -> str:
        """核心：将 WeasyPrint 解析出的各类 file:// URL 重新映射到 site 目录"""
        if not url.startswith("file://"):
            return url

        try:
            parsed = urllib.parse.urlparse(url)
            path_str = urllib.request.url2pathname(parsed.path)
            raw_path = pathlib.Path(path_str).resolve()
        except Exception:
            return url

        # 1. 如果已经在 site_root 内，且文件存在，直接返回
        if str(raw_path).startswith(str(self.site_root)) and raw_path.exists():
            return url

        # 2. 启发式路径搜索：处理绝对路径 /assets/... 或容器外部映射路径 /__w/...
        # 逐层剥离前缀，直到在 site_root 下找到匹配文件
        parts = raw_path.parts
        for i in range(len(parts)):
            # 跳过根路径标识 ('/', '\\', 'C:\\' 等)
            if parts[i] in ("/", "\\") or parts[i].endswith(":\\"):
                continue
            
            sub_path = pathlib.Path(*parts[i:])
            potential = self.site_root / sub_path
            if potential.exists():
                return potential.as_uri()

        return url

    def __call__(self, url: str, headers: Optional[Dict[str, str]] = None) -> URLFetcherResponse:
        """WeasyPrint 要求的调用接口"""
        # 1. 路径预修正
        target_url = self._resolve_local_url(url)

        # 2. 缓存命中检查
        if target_url in self.cache_pool:
            c = self.cache_pool[target_url]
            return URLFetcherResponse(
                url=c.get("url", target_url),
                body=io.BytesIO(c["content"]),
                mime_type=c.get("mime_type"),
                encoding=c.get("encoding"),
                redirected_url=c.get("redirected_url")
            )

        # 3. 真实拉取 (使用 WeasyPrint 内置的 default_url_fetcher)
        try:
            response = default_url_fetcher(target_url, headers=headers)
        except Exception as e:
            if not target_url.startswith(("http://", "https://")):
                print(f"\n   ⚠️ 资源获取失败 [{target_url}]: {e}", flush=True)
            raise e

        # 4. 入库并返回独占流
        if response is not None:
            try:
                # 获取内容流
                raw_body = getattr(response, "body", None) or getattr(response, "string", None) or getattr(response, "file_obj", None)
                
                content: Optional[bytes] = None
                if isinstance(raw_body, (bytes, str)):
                    content = raw_body if isinstance(raw_body, bytes) else raw_body.encode("utf-8")
                elif hasattr(raw_body, "read"):
                    content = raw_body.read()
                    try: raw_body.close()
                    except: pass
                
                if content is not None:
                    meta = {
                        "content": content,
                        "url": getattr(response, "url", target_url),
                        "mime_type": getattr(response, "mime_type", None),
                        "encoding": getattr(response, "encoding", None),
                        "redirected_url": getattr(response, "redirected_url", None)
                    }
                    self.cache_pool[target_url] = meta
                    return URLFetcherResponse(
                        url=meta["url"],
                        body=io.BytesIO(content),
                        mime_type=meta["mime_type"],
                        encoding=meta["encoding"],
                        redirected_url=meta["redirected_url"]
                    )
            except Exception:
                pass

        return response


class MlibDownloader:
    """PDF 下载器核心类 (V8 - 极致 URL 兼容版)"""

    def __init__(self, default_base_url: str = "./site"):
        # 根目录标准化
        self.site_root = pathlib.Path(default_base_url).resolve()
        self._task_queue: List[Tuple[str, str, Optional[str]]] = []
        
        # 缓存池
        self._url_cache_pool: Dict[str, Dict[str, Any]] = {}
        self._image_rendering_cache: Dict[str, Any] = {}
        
        # 引擎单例
        self._font_config = FontConfiguration()
        self._fetcher = CachedURLFetcher(self._url_cache_pool, self.site_root)
        self._page_css = CSS(string="@page { size: A4; margin: 1cm 0.75cm; }")

        print(f"🚀 MlibDownloader V8 初始化 | 站点根目录: {self.site_root}", flush=True)
        
        # 预热核心字体 (JSDelivr CDN)
        font_kit = "https://cdn.jsdelivr.net/npm/@raineblog/mkdocs-fontkit@latest/dist/fonts.min.css"
        self._warm_up_resource(font_kit)

    def _warm_up_resource(self, url: str) -> None:
        try:
            print(f"⏳ 正在预热核心资产: {url}", flush=True)
            self._fetcher(url)
            print(f"   ✅ 资产预热完成 (累计缓存: {format_size(self._fetcher.get_total_size())})", flush=True)
        except Exception as e:
            print(f"   ⚠️ 资产预热跳过: {e}", flush=True)

    def add_task(self, html_source: str, pdf_path: str, base_url: Optional[str] = None) -> None:
        # base_url 在此版本主要作为备选参考，核心路由由 site_root 驱动
        self._task_queue.append((html_source, pdf_path, base_url))
        print(f"➕ 添加任务: {pathlib.Path(pdf_path).name}", flush=True)

    def start_tasks(self) -> None:
        if not self._task_queue: return

        total = len(self._task_queue)
        print(f"\n▶️ 开始并行处理 {total} 份任务 | 初始缓存: {format_size(self._fetcher.get_total_size())}", flush=True)

        for i, (src, dst, _) in enumerate(self._task_queue, 1):
            start_t = time.time()
            dst_p = pathlib.Path(dst).resolve()
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            
            prefix = f"[{i}/{total}] "
            print(f"{prefix}正在渲染: {dst_p.name}...", end="", flush=True)

            try:
                src_p = pathlib.Path(src).expanduser().resolve()
                
                # 关键：base_url 必须指向 HTML 所在的真实目录
                # 这样 WeasyPrint 才能通过 eff_base 解析相对路径 (src="../../image.png")
                eff_base = src_p.parent.as_uri() + "/" if src_p.is_file() else src

                html_kwargs = {
                    "base_url": eff_base,
                    "url_fetcher": self._fetcher,
                    "media_type": "print"
                }
                html = HTML(filename=str(src_p), **html_kwargs) if src_p.is_file() else HTML(url=src, **html_kwargs)

                html.write_pdf(
                    target=str(dst_p),
                    stylesheets=[self._page_css],
                    font_config=self._font_config,
                    cache=self._image_rendering_cache,
                    full_fonts=False,
                    presentational_hints=True,
                    optimize_images=False # 关闭图片二次优化以换取速度
                )

                elapsed = time.time() - start_t
                status = f"✅ {dst_p.name} ({elapsed:.2f}s) | 缓存={format_size(self._fetcher.get_total_size())}"
                print(f"\r{prefix}{status}", flush=True)

            except Exception as e:
                print(f"\r{prefix}❌ 失败 {dst_p.name}: {e}", flush=True)

        print(f"\n🎉 批次处理完成 | 耗时: {time.time() - start_t:.2f}s", flush=True)
        self._task_queue.clear()

    def __del__(self):
        if hasattr(self, "_url_cache_pool") and self._url_cache_pool:
            print("\n� 周期统计: 缓存条数:", len(self._url_cache_pool), flush=True)


if __name__ == "__main__":
    print("=== MlibDownloader V8 Entry ===")

