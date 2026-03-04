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
            
        # 锚定模板目录到镜像内的绝对路径
        template_dir = os.environ.get("TEMPLATES_DIR", "/app/templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self.final_doc = fitz.open()
        self.page_offset = 0
        self.toc_data = []

    def extract_precise_toc(self, doc, offset):
        """
        根据 get_toc() 返回的初步目录，在对应页码进行文本定位，获取 y 坐标并偏移。
        调整层级以适应整体书籍结构 (Headings 设为 Level 3+)。
        """
        raw_toc = doc.get_toc()
        refined_toc = []
        
        for entry in raw_toc:
            lvl = entry[0]
            title = entry[1]
            page_1 = entry[2] 
            
            # 原始 PDF 的 H1 (lvl 1) 在合集中应设为 Level 3
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
                            if found_y is not None: break
                    if found_y is not None: break
                
                if found_y is not None:
                    dest["to"] = fitz.Point(0, found_y)
            
            refined_toc.append([new_lvl, title, new_page_1, dest])
            
        return refined_toc

    def get_english_filename(self):
        """从 nav.json 中查找对应的英文文件名"""
        nav_path = Path("D:/Github/blog/whk/config/nav.json")
        if nav_path.exists():
            try:
                with open(nav_path, "r", encoding="utf-8") as f:
                    nav_data = json.load(f)
                    for item in nav_data:
                        if item.get("title") == self.book_data.get("title"):
                            return item.get("export", {}).get("filename", f"{self.book_data['title']}.pdf")
            except Exception as e:
                print(f"Error reading nav.json: {e}")
        return f"{self.book_data['title']}.pdf"

    def process(self):
        book_title = self.book_data['title']
        print(f"Processing Book: {book_title}")
        temp_files = []
        
        # 1. 插入封面与装饰页
        decorative_pages = [
            ("cover", f"{book_title}_cover.pdf", "封面"),
            ("frontispiece", f"{book_title}_frontispiece.pdf", "扉页"),
            ("toc", f"{book_title}_toc.pdf", "目录")
        ]
        
        for key, fname, label in decorative_pages:
            p = self.output_dir / fname
            if p.exists():
                doc = fitz.open(p)
                self.final_doc.insert_pdf(doc)
                self.page_offset += len(doc)
                self.toc_data.append([1, label, self.page_offset - len(doc) + 1])
                doc.close()
                temp_files.append(p)

        # 2. 遍历章节
        for section in self.book_data["sections"]:
            sec_title = section['title']
            print(f"  Inserting Section: {sec_title}")
            
            # 章节首页 (Level 1)
            opener_path = self.output_dir / f"opener_{sec_title}.pdf"
            if opener_path.exists():
                opener_doc = fitz.open(opener_path)
                self.final_doc.insert_pdf(opener_doc)
                self.page_offset += len(opener_doc)
                self.toc_data.append([1, sec_title, self.page_offset - len(opener_doc) + 1])
                opener_doc.close()
                temp_files.append(opener_path)
            else:
                self.toc_data.append([1, sec_title, self.page_offset + 1])

            # 插入内容页 (Level 2)
            for sub in section["sections"]:
                sub_title = sub['title']
                content_path = self.book_json_path.parent / sub["path"]
                if not content_path.exists():
                     content_path = Path("site/build") / sub["path"]
                     
                if content_path.exists():
                    doc = fitz.open(content_path)
                    # 记录页面标题作为 Level 2 书签
                    self.toc_data.append([2, sub_title, self.page_offset + 1])
                    
                    # 提取并偏移章节内的 headings (Level 3+)
                    chapter_headings = self.extract_precise_toc(doc, self.page_offset)
                    self.toc_data.extend(chapter_headings)
                    
                    self.final_doc.insert_pdf(doc)
                    self.page_offset += len(doc)
                    doc.close()
                    temp_files.append(content_path)
                else:
                    print(f"    Warning: Content not found at {content_path}")

        # 3. 封底
        back_path = self.output_dir / f"{book_title}_backcover.pdf"
        if back_path.exists():
            doc = fitz.open(back_path)
            self.final_doc.insert_pdf(doc)
            self.page_offset += len(doc)
            self.toc_data.append([1, "封底", self.page_offset - len(doc) + 1])
            doc.close()
            temp_files.append(back_path)

        # 4. 设置最终目录并保存
        self.final_doc.set_toc(self.toc_data)
        
        final_filename = self.get_english_filename()
        output_file = self.output_dir / final_filename
        self.final_doc.save(output_file, deflate=True, garbage=4)
        self.final_doc.close()
        
        print(f"Final PDF saved to {output_file}")
        
        # 5. 清理
        print("Cleaning up temporary files...")
        for f in temp_files:
            try:
                if f.exists() and f != output_file:
                    f.unlink()
            except: pass
        # 清理 tex 文件
        for f in self.output_dir.glob("*.tex"): f.unlink()
        if (self.output_dir / "tex_tasks.txt").exists(): (self.output_dir / "tex_tasks.txt").unlink()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("book_json")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--merge", action="store_true")
    args = parser.parse_args()
    
    processor = PDFProcessor(args.book_json)
    if args.plan_only:
        # 仅生成 TeX 模板供后续容器编译
        print("Rendering TeX templates...")
        generated_tex_files = []
        book_title = processor.book_data.get('title', 'Unknown')
        
        common_data = {
            "title": book_title,
            "subtitle": processor.book_data.get("subtitle", ""),
            "authors": processor.book_data.get("authors", []),
            "info": processor.book_data.get("info", {})
        }

        # 1. 封面
        cover_tex = processor.jinja_env.get_template("cover.tex.j2").render(**common_data)
        cover_path = processor.output_dir / f"{book_title}_cover.tex"
        with open(cover_path, "w", encoding="utf-8") as f: f.write(cover_tex)
        generated_tex_files.append(str(cover_path))
            
        # 2. 扉页
        front_tex = processor.jinja_env.get_template("frontispiece.tex.j2").render(**common_data)
        front_path = processor.output_dir / f"{book_title}_frontispiece.tex"
        with open(front_path, "w", encoding="utf-8") as f: f.write(front_tex)
        generated_tex_files.append(str(front_path))

        # 3. 目录页 (简版概要)
        toc_outline = []
        for sec in processor.book_data["sections"]:
            toc_outline.append({"title": sec['title'], "page": "?"}) # 物理页码在 plan 阶段未知，通常填 ? 或略过
        toc_tex = processor.jinja_env.get_template("toc.tex.j2").render(toc_outline=toc_outline, **common_data)
        toc_path = processor.output_dir / f"{book_title}_toc.tex"
        with open(toc_path, "w", encoding="utf-8") as f: f.write(toc_tex)
        generated_tex_files.append(str(toc_path))

        # 4. 章首页
        for idx, section in enumerate(processor.book_data["sections"], 1):
            opener_tex = processor.jinja_env.get_template("opener.tex.j2").render(
                chapter_num=idx,
                chapter_title=section["title"]
            )
            opener_path = processor.output_dir / f"opener_{section['title']}.tex"
            with open(opener_path, "w", encoding="utf-8") as f: f.write(opener_tex)
            generated_tex_files.append(str(opener_path))
            
        # 5. 封底
        back_tex = processor.jinja_env.get_template("backcover.tex.j2").render(**common_data)
        back_path = processor.output_dir / f"{book_title}_backcover.tex"
        with open(back_path, "w", encoding="utf-8") as f: f.write(back_tex)
        generated_tex_files.append(str(back_path))

        # 写入任务列表供 CI 循环调用
        with open(processor.output_dir / "tex_tasks.txt", "w", encoding="utf-8") as f:
            for tf in generated_tex_files:
                f.write(f"{tf}\n")
        print(f"Generated {len(generated_tex_files)} TeX files. List saved to {processor.output_dir / 'tex_tasks.txt'}")
    if args.merge:
        # 执行最终的 PDF 合体
        processor.process()
