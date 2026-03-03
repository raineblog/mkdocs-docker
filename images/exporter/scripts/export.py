import subprocess
import yaml
import sys
import os
import shutil
from pathlib import Path
import json
import generate as mkut
from mlib_download import MlibDownloader

downloader = MlibDownloader()


def parse_yaml(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as file:
        text = file.read()
    return yaml.load(text, Loader=yaml.FullLoader)


def extract_title(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("# "):
                return line[2:].strip()
    return "无标题"


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def write_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def get_site_nav(nav):
    return [{item["title"]: item["children"]} for item in nav]


def clean_url(baseurl, filepath):
    return (
        baseurl.rstrip("/")
        + "/"
        + filepath.replace(".md", "/index.html").replace(
            "index/index.html", "index.html"
        )
    )


def process_top_level(info, sub_nav, baseurl, output_dir="site/build"):
    first_title = info["title"]

    sections = []
    for item in sub_nav:
        for second_title, third_list in item.items():
            section = {"title": second_title, "sections": []}
            for third_file in third_list:
                third_title = extract_title(
                    os.path.join("docs", third_file.replace("/", os.sep))
                )
                pdf_rel_path = os.path.join("pdfs", first_title, second_title, third_title + ".pdf")
                pdf_full_path = os.path.join(output_dir, pdf_rel_path)
                
                os.makedirs(os.path.dirname(pdf_full_path), exist_ok=True)
                
                html_url = clean_url(baseurl, third_file)
                downloader.add_task(html_url, pdf_rel_path)
                
                section["sections"].append({"title": third_title, "path": pdf_rel_path.replace("\\", "/")})
            sections.append(section)

    base_name = os.path.splitext(info["filename"])[0]

    write_json(
        os.path.join(output_dir, f"{base_name}.json"),
        {
            "title": info["title"],
            "subtitle": info["subtitle"],
            "authors": info["authors"],
            "info": info["info"],
            "sections": sections,
        },
    )

    return base_name


if __name__ == "__main__":
    nav = mkut.get_raw_nav()

    task_list = [(item["export"], item["children"]) for item in nav if "export" in item]

    for export, children in task_list:
        print(f"[{export['filename']}] {export['title']} {len(children)}")

    output_dir = "site/build"
    os.makedirs(output_dir, exist_ok=True)

    matrix_list = []
    for export, children in task_list:
        base_name = process_top_level(export, children, "./site", output_dir)
        matrix_list.append({"book": base_name})

    downloader.save_tasks(os.path.join(output_dir, "download.json"))

    # GitHub Action Matrix Output
    with open(os.environ.get("GITHUB_OUTPUT", "matrix.out"), "a", encoding="utf-8") as f:
        f.write(f"matrix={json.dumps(matrix_list, separators=(',', ':'))}\n")
    
    print("Build Success!")

