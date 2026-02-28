import os
import yaml
import json
import toml


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


def get_nav():
    nav_config = get_raw_nav()
    nav = []
    for item in nav_config:
        nav.append({item["title"]: item["children"]})
    return nav


def get_template(template_path):
    template_defaults = parse_yaml(template_path)
    project_config = load_json("config/project.json")
    template_defaults["theme"] |= project_config["theme"]
    return template_defaults


def get_site_template(copy_extra, template_name):
    info = load_json("config/project.json")["info"]
    if site_url := os.getenv("site_url"):
        info["site_url"] = site_url
    nav = {"nav": get_nav()}
    if copy_extra == True:
        info["extra"] = load_json("config/extra.json")
        if os.getenv("disable_giscus") == "true":
            info["extra"].pop("giscus", None)
    template_defaults = get_template("/app/templates/" + template_name)
    return info | template_defaults | nav


def write_site_template(config_path, copy_extra, template_name):
    config = get_site_template(copy_extra, template_name)
    config_path = config_path.strip()
    if config_path.endswith((".yml", ".yaml")):
        with open(config_path, "w", encoding="utf-8") as file:
            yaml.dump(config, file, allow_unicode=True, indent=4, sort_keys=False)
    elif config_path.endswith(".toml"):
        import toml

        with open(config_path, "w", encoding="utf-8") as file:
            toml.dump(config, file)
    elif config_path.endswith(".json"):
        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(config, file, allow_unicode=True, indent=4, sort_keys=False)
