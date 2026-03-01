# mlib_download.py
# WeasyPrint HTML-to-PDF 下载器 - 极致性能与现代架构版 (V8.1)
# 针对 WeasyPrint 68.1+ 深度优化，解决 I/O 冲突、路径寻址与缓存漏记故障

import io
import re
import time
import pathlib
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple, MutableMapping
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from weasyprint.urls import URLFetcherResponse, default_url_fetcher


def format_size(size_bytes: int) -> str:
    """格式化字节数为人类可读格式"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


class CachedURLFetcher:
    """
    极致性能与路径兼容的现代 Fetcher (V8.1)
    - 兼容 WeasyPrint 各个版本的 default_url_fetcher 签名 (修复 headers 传参报错)
    - 智能路径重定向：由网站根目录 site_root 驱动
    - 共享内存缓存：确保多任务间资源复用，彻底解决“缓存=0 B”问题
    """

    def __init__(self, cache_pool: MutableMapping[str, Dict[str, Any]], site_root: pathlib.Path):
        self.cache_pool = cache_pool
        self.site_root = site_root.resolve()

    def get_total_size(self) -> int:
        return sum(len(item["content"]) for item in self.cache_pool.values() if "content" in item)

    def _resolve_local_url(self, url: str) -> str:
        """解析本地 file:// URL 并尝试重定向到 site 目录"""
        if not url.startswith("file://"):
            return url

        try:
            parsed = urllib.parse.urlparse(url)
            path_str = urllib.request.url2pathname(parsed.path)
            raw_path = pathlib.Path(path_str).resolve()
        except Exception:
            return url

        # 1. 已经在 site_root 内且存在，直接返回
        if str(raw_path).startswith(str(self.site_root)) and raw_path.exists():
            return url

        # 2. 启发式：剥离前缀匹配 site_root
        # 针对 GitHub Runner /__w/ 路径或绝对路径 /assets 重定向到 ./site/
        parts = raw_path.parts
        for i in range(len(parts)):
            if parts[i] in ("/", "\\") or parts[i].endswith(":\\"):
                continue
            potential = self.site_root / pathlib.Path(*parts[i:])
            if potential.exists():
                return potential.as_uri()

        return url

    def __call__(self, url: str, headers: Optional[Dict[str, str]] = None) -> URLFetcherResponse:
        """WeasyPrint 核心调用入口"""
        # 1. 内部重定向 (处理绝对路径偏移)
        target_url = self._resolve_local_url(url)

        # 2. 命中全局共享缓存
        if target_url in self.cache_pool:
            c = self.cache_pool[target_url]
            return URLFetcherResponse(
                url=c.get("url", target_url),
                body=io.BytesIO(c["content"]),
                mime_type=c.get("mime_type"),
                encoding=c.get("encoding"),
                redirected_url=c.get("redirected_url")
            )

        # 3. 物理拉取 (自动适配 headers 签名)
        response = None
        try:
            try:
                # 尝试完整签名调用
                response = default_url_fetcher(target_url, headers=headers)
            except TypeError:
                # 降级：部分 WeasyPrint 版本的默认 fetcher 不接受 headers
                response = default_url_fetcher(target_url)
        except Exception as e:
            # 仅上报本地资源 404，网络资源允许静默失败
            if target_url.startswith("file://"):
                print(f"\n   ⚠️ 资源获取失败 [{target_url}]: {e}", flush=True)
            raise e

        # 4. 入库并返回独占流
        if response is not None:
            try:
                is_dict = isinstance(response, dict)
                # 提取 Body
                raw_body = (
                    (response.get("string") or response.get("file_obj"))
                    if is_dict
                    else (getattr(response, "body", None) or getattr(response, "string", None) or getattr(response, "file_obj", None))
                )
                
                content: Optional[bytes] = None
                if isinstance(raw_body, (bytes, str)):
                    content = raw_body if isinstance(raw_body, bytes) else raw_body.encode("utf-8")
                elif hasattr(raw_body, "read"):
                    content = raw_body.read()
                    if hasattr(raw_body, "close"):
                        try: raw_body.close()
                        except: pass
                
                if content is not None:
                    meta = {
                        "content": content,
                        "url": response.get("url", target_url) if is_dict else getattr(response, "url", target_url),
                        "mime_type": response.get("mime_type") if is_dict else getattr(response, "mime_type", None),
                        "encoding": response.get("encoding") if is_dict else getattr(response, "encoding", None),
                        "redirected_url": response.get("redirected_url") if is_dict else getattr(response, "redirected_url", None)
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
    """PDF 下载器核心调度类 (V8.1)"""

    def __init__(self, default_base_url: str = "./site"):
        self.site_root = pathlib.Path(default_base_url).resolve()
        self._task_queue: List[Tuple[str, str, Optional[str]]] = []
        
        # 全局常驻资源池
        self._url_cache_pool: Dict[str, Dict[str, Any]] = {}
        self._image_rendering_cache: Dict[str, Any] = {}
        
        # 引擎配置单例
        self._font_config = FontConfiguration()
        self._fetcher = CachedURLFetcher(self._url_cache_pool, self.site_root)
        self._page_css = CSS(string="@page { size: A4; margin: 1cm 0.75cm; }")

        print(f"🚀 MlibDownloader V8.1 初始化 | 站点根目录: {self.site_root}", flush=True)
        
        # 预热字体 (CDN)
        font_kit = "https://cdn.jsdelivr.net/npm/@raineblog/mkdocs-fontkit@latest/dist/fonts.min.css"
        self._warm_up_resource(font_kit)

    def _warm_up_resource(self, url: str) -> None:
        try:
            print(f"⏳ 正在预热核心资产: {url}", flush=True)
            self._fetcher(url)
            print(f"   ✅ 预热完成 (累计缓存: {format_size(self._fetcher.get_total_size())})", flush=True)
        except Exception as e:
            print(f"   ⚠️ 资产预热跳过: {e}", flush=True)

    def add_task(self, html_source: str, pdf_path: str, base_url: Optional[str] = None) -> None:
        self._task_queue.append((html_source, pdf_path, base_url))
        print(f"➕ 添加任务: {pathlib.Path(pdf_path).name}", flush=True)

    def start_tasks(self) -> None:
        if not self._task_queue: return

        batch_start = time.time()
        total = len(self._task_queue)
        print(f"\n▶️ 开始渲染 {total} 个 PDF | 初始缓存: {format_size(self._fetcher.get_total_size())}", flush=True)

        for i, (src, dst, _) in enumerate(self._task_queue, 1):
            start_t = time.time()
            dst_p = pathlib.Path(dst).resolve()
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            
            prefix = f"[{i}/{total}] "
            print(f"{prefix}正在渲染: {dst_p.name}...", end="", flush=True)

            try:
                src_p = pathlib.Path(src).expanduser().resolve()
                
                # 动态 base_url: 指向该 HTML 实际所在的目录，支持相对路径
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
                    optimize_images=False
                )

                elapsed = time.time() - start_t
                status = f"✅ {dst_p.name} ({elapsed:.2f}s) | 缓存={format_size(self._fetcher.get_total_size())}"
                print(f"\r{prefix}{status}", flush=True)

            except Exception as e:
                print(f"\r{prefix}❌ 失败 {dst_p.name}: {e}", flush=True)

        total_elapsed = time.time() - batch_start
        print(f"\n🎉 批次生产完成 | 总数: {total} 份 | 总耗时: {total_elapsed:.2f}s | 平均: {total_elapsed/total:.2f}s/pdf", flush=True)
        self._report_stats()
        self._task_queue.clear()

    def _report_stats(self) -> None:
        size = self._fetcher.get_total_size()
        print(f"📊 共享资源池摘要: {len(self._url_cache_pool)} 项已缓存 | 占用内存: {format_size(size)}", flush=True)

    def __del__(self):
        pass


if __name__ == "__main__":
    print("=== MlibDownloader V8.1 Load Test ===")
