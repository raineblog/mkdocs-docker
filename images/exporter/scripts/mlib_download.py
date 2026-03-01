# mlib_download.py
# WeasyPrint HTML-to-PDF 下载器 - 极致性能与现代架构版 (V8.3)
# 针对 WeasyPrint 68.1+ 深度优化，解决路径重定向与缓存命中统计问题

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


class CachedURLFetcher:
    """
    极致性能与路径兼容的现代 Fetcher (V8.3)
    - 兼容 WeasyPrint 各个版本的 default_url_fetcher 响应格式 (dict/object)
    - 智能路径重定向：由站点根目录 site_root 驱动，解决 Github Runner 路径偏移
    - 资源计数统计：替代不可靠的体积统计
    """

    def __init__(self, cache_pool: MutableMapping[str, Dict[str, Any]], site_root: pathlib.Path):
        self.cache_pool = cache_pool
        self.site_root = site_root.resolve()

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

        # 2. 启发式：逐层剥离路径前缀查找 site 目录下的对应资源
        parts = raw_path.parts
        for i in range(len(parts)):
            if parts[i] in ("/", "\\") or parts[i].endswith(":\\"):
                continue
            potential = self.site_root / pathlib.Path(*parts[i:])
            if potential.exists():
                return potential.as_uri()

        return url

    def __call__(self, url: str, headers: Optional[Dict[str, str]] = None) -> URLFetcherResponse:
        # 1. 路径重定向
        target_url = self._resolve_local_url(url)

        # 2. 共享缓存命中
        if target_url in self.cache_pool:
            c = self.cache_pool[target_url]
            return URLFetcherResponse(
                url=c.get("url", target_url),
                body=io.BytesIO(c["content"]),
                mime_type=c.get("mime_type"),
                encoding=c.get("encoding"),
                redirected_url=c.get("redirected_url")
            )

        # 3. 物理拉取 (适配不同版本的 headers 传参)
        response = None
        try:
            try:
                response = default_url_fetcher(target_url, headers=headers)
            except TypeError:
                response = default_url_fetcher(target_url)
        except Exception as e:
            if target_url.startswith("file://"):
                print(f"\n   ⚠️ 资源获取失败 [{target_url}]: {e}", flush=True)
            raise e

        # 4. 解析并入库
        if response is not None:
            try:
                is_dict = isinstance(response, dict)
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
    """PDF 下载器核心调度类 (V8.3 - 效率优化版)"""

    def __init__(self, default_base_url: str = "./site"):
        self.site_root = pathlib.Path(default_base_url).resolve()
        self._task_queue: List[Tuple[str, str, Optional[str]]] = []
        
        # 全局常驻存储
        self._url_cache_pool: Dict[str, Dict[str, Any]] = {}
        self._image_rendering_cache: Dict[str, Any] = {}
        
        # 引擎单例
        self._font_config = FontConfiguration()
        self._fetcher = CachedURLFetcher(self._url_cache_pool, self.site_root)
        
        # 预设通用 CSS (避免重复解析)
        self._base_stylesheets = [
            CSS(string="@page { size: A4; margin: 1cm 0.75cm; }")
        ]

        print(f"🚀 MlibDownloader V8.3 初始化 | 站点根目录: {self.site_root}", flush=True)
        
        # 预热核心字体
        self._warm_up("https://cdn.jsdelivr.net/npm/@raineblog/mkdocs-fontkit@latest/dist/fonts.min.css")

    def _warm_up(self, url: str) -> None:
        try:
            print(f"⏳ 正在预热核心资产: {url}", flush=True)
            self._fetcher(url)
            print(f"   ✅ 预热完成 (当前缓存池: {len(self._url_cache_pool)} 项资源)", flush=True)
        except Exception as e:
            print(f"   ⚠️ 资产预热跳过: {e}", flush=True)

    def add_task(self, html_source: str, pdf_path: str, base_url: Optional[str] = None) -> None:
        self._task_queue.append((html_source, pdf_path, base_url))
        print(f"➕ 添加任务: {pathlib.Path(pdf_path).name}", flush=True)

    def start_tasks(self) -> None:
        if not self._task_queue: return

        batch_start = time.time()
        total = len(self._task_queue)
        print(f"\n▶️ 开始顺序渲染 {total} 个 PDF | 初始缓存: {len(self._url_cache_pool)} 项", flush=True)

        for i, (src, dst, _) in enumerate(self._task_queue, 1):
            task_start = time.time()
            dst_p = pathlib.Path(dst).resolve()
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            
            prefix = f"[{i}/{total}] "
            print(f"{prefix}渲染中: {dst_p.name}...", end="", flush=True)

            try:
                src_p = pathlib.Path(src).expanduser().resolve()
                eff_base = src_p.parent.as_uri() + "/" if src_p.is_file() else src

                # 核心：使用预置 fetcher 和缓存池
                html = HTML(
                    filename=str(src_p) if src_p.is_file() else None,
                    url=src if not src_p.is_file() else None,
                    base_url=eff_base,
                    url_fetcher=self._fetcher,
                    media_type="print"
                )

                # 优化渲染参数
                html.write_pdf(
                    target=str(dst_p),
                    stylesheets=self._base_stylesheets,
                    font_config=self._font_config,
                    cache=self._image_rendering_cache,
                    full_fonts=False, # 字体子集化关键性能点
                    presentational_hints=True,
                    optimize_images=False # 速度优先
                )

                elapsed = time.time() - task_start
                print(f"\r{prefix}✅ {dst_p.name} ({elapsed:.2f}s) | 缓存={len(self._url_cache_pool)}项", flush=True)

            except Exception as e:
                print(f"\r{prefix}❌ 失败 {dst_p.name}: {e}", flush=True)

        total_elapsed = time.time() - batch_start
        print(f"\n🎉 批次处理完成 | 总耗时: {total_elapsed:.2f}s | 平均: {total_elapsed/total:.2f}s/pdf", flush=True)
        print(f"📊 最终统计: 缓存池共计 {len(self._url_cache_pool)} 项资源，图片缓存 {len(self._image_rendering_cache)} 项", flush=True)
        self._task_queue.clear()


if __name__ == "__main__":
    print("=== MlibDownloader V8.3 Engine ===")
