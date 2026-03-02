# import os
import yaml
import json
# import toml


def parse_yaml(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as file:
        text = file.read()
    return yaml.load(text, Loader=yaml.FullLoader)


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def get_raw_nav():
    nav_config = load_json("config/nav.json")
    return nav_config


def get_template(template_path):
    template_defaults = parse_yaml(template_path)
    project_config = load_json("config/project.json")
    template_defaults["theme"] |= project_config["theme"]
    return template_defaults


if __name__ == "__main__":
    info = load_json("config/project.json")["info"]
    template_defaults = get_template("/app/templates/template.yml")
    config = info | template_defaults
    config['nav'] = []
    with open("mkdocs.yml", "w", encoding="utf-8") as file:
        yaml.dump(config, file, allow_unicode=True, indent=4, sort_keys=False)
