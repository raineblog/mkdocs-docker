import fitz
import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

class PDFProcessor:
    def __init__(self, book_json_path, output_dir="build"):
        self.book_json_path = Path(book_json_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.book_json_path, "r", encoding="utf-8") as f:
            self.book_data = json.load(f)
            
        template_dir = os.environ.get("TEMPLATES_DIR", "/app/templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self.final_doc = fitz.open()
        self.page_offset = 0
        self.toc_data = [] # [[lvl, title, page, dest]]
        self.skip_decoration_pages = set() # 1-based
        self.book_meta = {}

    def extract_precise_toc(self, doc, offset):
        raw_toc = doc.get_toc()
        refined_toc = []
        for entry in raw_toc:
            lvl, title, page_1 = entry[0], entry[1], entry[2]
            new_lvl = lvl + 2
            new_page_1 = page_1 + offset
            dest = {"kind": fitz.LINK_GOTO, "page": new_page_1 - 1, "to": fitz.Point(0, 0)}
            page_0 = page_1 - 1
            if 0 <= page_0 < len(doc):
                found_y = None
                page_obj = doc[page_0]
                blocks = page_obj.get_text("dict")["blocks"]
                target_title_norm = title.strip().lower()
                for b in blocks:
                    if "lines" in b:
                        for line in b["lines"]:
                            for s in line["spans"]:
                                if s["text"].strip().lower() == target_title_norm:
                                    found_y = s["bbox"][1]
                                    break
                            if found_y is not None:
                                break
                        if found_y is not None:
                            break
                    if found_y is not None:
                        break
                if found_y is not None:
                    dest["to"] = fitz.Point(0, found_y)
            refined_toc.append([new_lvl, title, new_page_1, dest])
        return refined_toc

    def sanitize_toc(self, toc):
        """
        确保目录层级连续，不出现跳级 (例如从 1 直接到 3)。
        PyMuPDF 要求每个条目的级别不能比前一个条目大超过 1。
        """
        if not toc: return []
        new_toc = []
        last_lvl = 0 
        for entry in toc:
            lvl, title, page = entry[0], entry[1], entry[2]
            # 第一个条目必须是级别 1
            if not new_toc:
                lvl = 1
            elif lvl > last_lvl + 1:
                lvl = last_lvl + 1
            
            if len(entry) > 3:
                new_toc.append([lvl, title, page, entry[3]])
            else:
                new_toc.append([lvl, title, page])
            last_lvl = lvl
        return new_toc

    def add_toc_links(self, toc_page_num):
        if toc_page_num > len(self.final_doc):
            return
        page = self.final_doc[toc_page_num - 1]
        blocks = page.get_text("blocks")
        for ent in self.toc_data:
            lvl, title, target_page = ent[0], ent[1], ent[2]
            if lvl > 2:
                continue
            for b in blocks:
                if title in b[4]:
                    rect = fitz.Rect(b[:4])
                    page.insert_link({"kind": fitz.LINK_GOTO, "page": target_page - 1, "from": rect})
                    break

    def ensure_parity(self, target_parity):
        current_page = self.page_offset + 1
        if current_page % 2 != target_parity:
            self.final_doc.new_page(width=fitz.paper_size("a4")[0], height=fitz.paper_size("a4")[1])
            self.page_offset += 1
            self.skip_decoration_pages.add(self.page_offset)
            return True
        return False

    def draw_decorations(self, doc, start_page_num, book_title, section_title):
        font_name = "china-ss" 
        for i in range(len(doc)):
            page = doc[i]
            abs_page = start_page_num + i
            if abs_page in self.skip_decoration_pages:
                continue
            is_odd = abs_page % 2 != 0
            footer_font = "helv"
            footer_size = 9
            footer_y = page.rect.height - 30
            footer_text = f"{abs_page}"
            page.insert_text((page.rect.width / 2 - 5, footer_y), footer_text, fontsize=footer_size, fontname=footer_font, color=(0.4, 0.4, 0.4))
            header_y = 35
            line_y = 45
            header_size = 9
            color = (0.5, 0.5, 0.5)
            if is_odd:
                text = section_title
                tw = fitz.get_text_length(text, fontname=font_name, fontsize=header_size)
                page.insert_text((page.rect.width - tw - 40, header_y), text, fontsize=header_size, fontname=font_name, color=color)
            else:
                text = book_title
                page.insert_text((40, header_y), text, fontsize=header_size, fontname=font_name, color=color)
            page.draw_line((40, line_y), (page.rect.width - 40, line_y), color=(0.8, 0.8, 0.8), width=0.4)

    def get_english_filename(self):
        """从 nav.json 中查找对应的英文文件名"""
        # 增加搜索范围，包括常见的挂载路径和父目录
        paths = [
            Path("D:/Github/blog/whk/config/nav.json"),
            Path("/github/workspace/nav.json"), # GHA 常用
            Path("config/nav.json"),
            Path("../config/nav.json"),
            Path("/app/config/nav.json"),
        ]
        # 尝试根据当前目录向上查找多级
        curr = Path.cwd()
        for _ in range(3):
            paths.append(curr / "config/nav.json")
            curr = curr.parent

        active_path = None
        for p in paths:
            if p.exists():
                active_path = p
                break
        
        if active_path:
            try:
                print(f"  Found nav.json at {active_path}")
                with open(active_path, "r", encoding="utf-8") as f:
                    nav_data = json.load(f)
                    # 支持直接列表或者包含在 'nav' 键中
                    items = nav_data if isinstance(nav_data, list) else nav_data.get("nav", [])
                    for item in items:
                        if item.get("title") == self.book_data.get("title"):
                            return item.get("export", {}).get("filename", f"{self.book_data['title']}.pdf")
            except Exception as e:
                print(f"  Warning: Could not parse nav.json: {e}")
        else:
            print("  Warning: nav.json not found in searched paths.")
        
        print(f"  Fallback to original title: {self.book_data.get('title')}.pdf")
        return f"{self.book_data['title']}.pdf"

    def process(self):
        book_title = self.book_data['title']
        temp_files = []
        output_file = self.output_dir / self.get_english_filename()
        decorative_pages = [("cover", f"{book_title}_cover.pdf", "封面", 1), ("frontispiece", f"{book_title}_frontispiece.pdf", "扉页", 0), ("toc", f"{book_title}_toc.pdf", "目录", 1)]
        toc_page_num = 0
        for key, fname, label, target_parity in decorative_pages:
            self.ensure_parity(target_parity)
            p = self.output_dir / fname
            if p.exists():
                doc = fitz.open(p)
                p_start = self.page_offset + 1
                if key == "toc":
                    toc_page_num = p_start
                self.skip_decoration_pages.add(p_start)
                self.final_doc.insert_pdf(doc)
                self.page_offset += len(doc)
                self.toc_data.append([1, label, p_start])
                doc.close()
                temp_files.append(p)
        for section in self.book_data["sections"]:
            sec_title = section['title']
            self.ensure_parity(1)
            opener_path = self.output_dir / f"opener_{sec_title}.pdf"
            if opener_path.exists():
                opener_doc = fitz.open(opener_path)
                p_start = self.page_offset + 1
                self.skip_decoration_pages.add(p_start)
                self.final_doc.insert_pdf(opener_doc)
                self.page_offset += len(opener_doc)
                self.toc_data.append([1, sec_title, p_start])
                opener_doc.close()
                temp_files.append(opener_path)
            else:
                self.toc_data.append([1, sec_title, self.page_offset + 1])
            for sub in section["sections"]:
                sub_title = sub['title']
                self.ensure_parity(0)
                content_path = self.book_json_path.parent / sub["path"]
                if not content_path.exists():
                    content_path = Path("site/build") / sub["path"]
                if content_path.exists():
                    doc = fitz.open(content_path)
                    chapter_headings = self.extract_precise_toc(doc, self.page_offset)
                    main_title_norm = sub_title.strip().lower()
                    if chapter_headings and chapter_headings[0][1].strip().lower() == main_title_norm:
                        chapter_headings[0][0] = 2
                        self.toc_data.extend(chapter_headings)
                    else:
                        self.toc_data.append([2, sub_title, self.page_offset + 1])
                        self.toc_data.extend(chapter_headings)
                    self.draw_decorations(doc, self.page_offset + 1, book_title, sec_title)
                    self.final_doc.insert_pdf(doc)
                    self.page_offset += len(doc)
                    doc.close()
                    temp_files.append(content_path)
        
        # 3. 封底 (确保在偶数页)
        self.ensure_parity(0)
        back_path = self.output_dir / f"{book_title}_backcover.pdf"
        if back_path.exists():
            doc = fitz.open(back_path)
            p_start = self.page_offset + 1
            self.skip_decoration_pages.add(p_start)
            self.final_doc.insert_pdf(doc)
            self.page_offset += len(doc)
            self.toc_data.append([1, "封底", p_start])
            doc.close()
            temp_files.append(back_path)
        
        # 4. 设置最终目录前，先净化级别
        print("Finalizing TOC and links...")
        self.toc_data = self.sanitize_toc(self.toc_data)
        self.final_doc.set_toc(self.toc_data)
        if toc_page_num > 0: self.add_toc_links(toc_page_num)
        self.final_doc.save(output_file, deflate=True, garbage=4)
        self.final_doc.close()
        print(f"Final PDF saved to {output_file}")
        resolved_output = output_file.resolve()
        for f in temp_files:
            try:
                if f.exists() and f.resolve() != resolved_output:
                    f.unlink()
            except Exception:
                pass
        for f in self.output_dir.glob("*.tex"):
            try:
                f.unlink()
            except Exception:
                pass
        if (self.output_dir / "tex_tasks.txt").exists():
            (self.output_dir / "tex_tasks.txt").unlink()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("book_json")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--merge", action="store_true")
    args = parser.parse_args()
    processor = PDFProcessor(args.book_json)
    if args.plan_only:
        generated_tex_files = []
        book_title = processor.book_data.get('title', 'Unknown')
        est_offset = 3 
        common_data = {"title": book_title, "subtitle": processor.book_data.get("subtitle", ""), "authors": processor.book_data.get("authors", []), "info": processor.book_data.get("info", {})}
        cover_path = processor.output_dir / f"{book_title}_cover.tex"
        with open(cover_path, "w", encoding="utf-8") as f: f.write(processor.jinja_env.get_template("cover.tex.j2").render(**common_data))
        generated_tex_files.append(str(cover_path))
        front_path = processor.output_dir / f"{book_title}_frontispiece.tex"
        with open(front_path, "w", encoding="utf-8") as f: f.write(processor.jinja_env.get_template("frontispiece.tex.j2").render(**common_data))
        generated_tex_files.append(str(front_path))
        toc_outline = []
        running_page = est_offset + 1
        for section in processor.book_data["sections"]:
            if running_page % 2 == 0: running_page += 1
            entry = {"title": section['title'], "page": running_page, "children": []}
            running_page += 1
            for sub in section["sections"]:
                if running_page % 2 != 0: running_page += 1
                content_path = processor.book_json_path.parent / sub["path"]
                if not content_path.exists(): content_path = Path("site/build") / sub["path"]
                content_page_count = 0
                if content_path.exists():
                    try:
                        with fitz.open(content_path) as doc:
                            content_page_count = len(doc)
                    except Exception:
                        pass
                entry["children"].append({"title": sub['title'], "page": running_page})
                running_page += content_page_count
            toc_outline.append(entry)
        toc_tex = processor.jinja_env.get_template("toc.tex.j2").render(toc_outline=toc_outline, **common_data)
        toc_path = processor.output_dir / f"{book_title}_toc.tex"
        with open(toc_path, "w", encoding="utf-8") as f:
            f.write(toc_tex)
        generated_tex_files.append(str(toc_path))
        for idx, section in enumerate(processor.book_data["sections"], 1):
            opener_path = processor.output_dir / f"opener_{section['title']}.tex"
            with open(opener_path, "w", encoding="utf-8") as f:
                f.write(processor.jinja_env.get_template("opener.tex.j2").render(chapter_num=idx, chapter_title=section["title"]))
            generated_tex_files.append(str(opener_path))
        back_path = processor.output_dir / f"{book_title}_backcover.tex"
        with open(back_path, "w", encoding="utf-8") as f:
            f.write(processor.jinja_env.get_template("backcover.tex.j2").render(**common_data))
        generated_tex_files.append(str(back_path))
        with open(processor.output_dir / "tex_tasks.txt", "w", encoding="utf-8") as f:
            for tf in generated_tex_files:
                f.write(f"{tf}\n")
    if args.merge:
        processor.process()
