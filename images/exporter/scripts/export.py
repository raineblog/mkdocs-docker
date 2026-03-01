import subprocess
import yaml
import sys
import os
import shutil
from pathlib import Path
import json
import generate as mkut
from mlib_download import MlibDownloader

downloader = MlibDownloader(default_base_url="./site/")


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





def process_top_level(info, sub_nav, baseurl):
    first_title = info["title"]
    first_out = os.path.join("cache", first_title)
    os.makedirs(first_out, exist_ok=True)

    sections = []
    for item in sub_nav:
        for second_title, third_list in item.items():
            second_out = os.path.join(first_out, second_title)
            os.makedirs(second_out, exist_ok=True)
            section = {"title": second_title, "sections": []}
            for third_file in third_list:
                third_title = extract_title(
                    os.path.join("docs", third_file.replace("/", os.sep))
                )
                pdf_path = os.path.join(first_out, second_title, third_title + ".pdf")
                html_url = clean_url(baseurl, third_file)
                downloader.add_task(html_url, pdf_path)
                section["sections"].append({"title": third_title, "path": pdf_path})
            sections.append(section)

    downloader.start_tasks()

    relative_sections = []
    for section in sections:
        rel_sec = {"title": section["title"], "sections": []}
        for sub in section["sections"]:
            rel_sec["sections"].append(
                {
                    "title": sub["title"],
                    "path": sub["path"].replace("cache/", "", 1).replace("\\", "/"),
                }
            )
        relative_sections.append(rel_sec)

    write_json(
        "cache/toc.json",
        {
            "title": info["title"],
            "subtitle": info["subtitle"],
            "authors": info["authors"],
            "info": info["info"],
            "sections": relative_sections,
        },
    )

    shutil.copy("/app/templates/template.tex", "cache/main.tex")
    
    base_name = os.path.splitext(info["filename"])[0]
    tar_path = os.path.join("build", f"{base_name}.tar.zst")
    print(f"[*] Packaging {base_name} tex environment...")
    
    cmd = f"tar -cf - -C cache . | zstd -T0 -3 > {tar_path}"
    subprocess.run(cmd, shell=True, check=True)

    shutil.rmtree("cache")


if __name__ == "__main__":
    nav = mkut.get_raw_nav()

    task_list = [(item["export"], item["children"]) for item in nav if "export" in item]

    for export, children in task_list:
        print(f"[{export['filename']}] {export['title']} {len(children)}")

    # mkut.write_site_template("mkdocs.yml", False, "template.yml")
    # subprocess.run("mkdocs build --clean", shell=True, check=True)
    os.makedirs("build", exist_ok=True)

    for export, children in task_list:
        process_top_level(export, children, "./site")

    print("Build Success!")
