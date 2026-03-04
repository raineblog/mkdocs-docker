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
        """
        # PyMuPDF get_toc() 可能返回 3 或 4 个元素的列表: [lvl, title, page, (dest_dict)]
        raw_toc = doc.get_toc()
        refined_toc = []
        
        for entry in raw_toc:
            lvl = entry[0]
            title = entry[1]
            page_1 = entry[2] # 1st-based page in current doc
            
            # 默认目标 (整页跳转)
            # PyMuPDF set_toc 期待 dest 为字典，或者 None (默认跳转到页顶)
            new_page_1 = page_1 + offset
            dest = {"kind": fitz.LINK_GOTO, "page": new_page_1 - 1, "to": fitz.Point(0, 0)}
            
            # 尝试在特定页面查找标题以获取精确 Y 坐标
            page_0 = page_1 - 1
            if 0 <= page_0 < len(doc):
                found_y = None
                page_obj = doc[page_0]
                # get_text("dict") 包含了文本块的边界框
                blocks = page_obj.get_text("dict")["blocks"]
                target_title_norm = title.strip().lower()
                
                for b in blocks:
                    if "lines" in b:
                        for line in b["lines"]:
                            for s in line["spans"]:
                                if s["text"].strip().lower() == target_title_norm:
                                    found_y = s["bbox"][1] # y0 (top coordinate)
                                    break
                            if found_y is not None: break
                    if found_y is not None: break
                
                if found_y is not None:
                    dest["to"] = fitz.Point(0, found_y)
                else:
                    print(f"    Note: Could not find precise position for '{title}' on page {page_1}, using page top.")
            
            refined_toc.append([lvl, title, new_page_1, dest])
            
        return refined_toc

    def process(self):
        print(f"Processing Book: {self.book_data['title']}")
        
        # 1. 准备装饰页 (TeX)
        # TODO: 渲染模板并调用 xelatex (此处假设已有编译好的 PDF 或通过外部步骤完成)
        
        # 2. 合成逻辑
        # 插入封面 (假设名称为 cover.pdf)
        cover_path = self.output_dir / f"{self.book_data['title']}_cover.pdf"
        if cover_path.exists():
            cover_doc = fitz.open(cover_path)
            self.final_doc.insert_pdf(cover_doc)
            self.page_offset += len(cover_doc)
            cover_doc.close()

        # 遍历章节
        for section in self.book_data["sections"]:
            print(f"  Inserting Section: {section['title']}")
            
            # 插入章首页 (TeX 产物)
            opener_path = self.output_dir / f"opener_{section['title']}.pdf"
            if opener_path.exists():
                opener_doc = fitz.open(opener_path)
                self.final_doc.insert_pdf(opener_doc)
                self.page_offset += len(opener_doc)
                opener_doc.close()
                self.toc_data.append([1, section['title'], self.page_offset]) # 章级目录

            # 插入内容页
            for sub in section["sections"]:
                # 尝试从 JSON 所在目录查找，或者使用绝对 site/build 路径
                content_path = self.book_json_path.parent / sub["path"]
                if not content_path.exists():
                     content_path = Path("site/build") / sub["path"]
                     
                if content_path.exists():
                    doc = fitz.open(content_path)
                    # 提取并偏移章节内的书签
                    chapter_toc = self.extract_precise_toc(doc, self.page_offset)
                    self.toc_data.extend(chapter_toc)
                    
                    self.final_doc.insert_pdf(doc)
                    self.page_offset += len(doc)
                    doc.close()
                else:
                    print(f"    Warning: Content not found at {content_path}")

        # 3. 设置最终目录
        self.final_doc.set_toc(self.toc_data)
        
        # 4. 保存
        output_file = self.output_dir / f"{self.book_data['title']}.pdf"
        self.final_doc.save(output_file, deflate=True, garbage=4)
        self.final_doc.close()
        print(f"Final PDF saved to {output_file}")

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
        
        # 渲染封面
        cover_filename = f"{processor.book_data.get('title', 'Unknown')}_cover.tex"
        cover_tex = processor.jinja_env.get_template("cover.tex.j2").render(
            title=processor.book_data.get("title", "Unknown"),
            subtitle=processor.book_data.get("subtitle", ""),
            authors=processor.book_data.get("authors", [])
        )
        cover_path = processor.output_dir / cover_filename
        with open(cover_path, "w", encoding="utf-8") as f:
            f.write(cover_tex)
        generated_tex_files.append(str(cover_path))
            
        # 渲染章首页
        for idx, section in enumerate(processor.book_data["sections"], 1):
            opener_filename = f"opener_{section['title']}.tex"
            opener_tex = processor.jinja_env.get_template("opener.tex.j2").render(
                chapter_num=idx,
                chapter_title=section["title"]
            )
            opener_path = processor.output_dir / opener_filename
            with open(opener_path, "w", encoding="utf-8") as f:
                f.write(opener_tex)
            generated_tex_files.append(str(opener_path))
            
        # 写入任务列表供 CI 循环调用
        with open(processor.output_dir / "tex_tasks.txt", "w", encoding="utf-8") as f:
            for tf in generated_tex_files:
                f.write(f"{tf}\n")
        print(f"Generated {len(generated_tex_files)} TeX files. List saved to {processor.output_dir / 'tex_tasks.txt'}")
    if args.merge:
        # 执行最终的 PDF 合体
        processor.process()
