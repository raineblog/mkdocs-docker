import yaml
import json
import os
from pathlib import Path

script_dir = Path(__file__).parent.resolve()

def parse_yaml(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return yaml.load(text, Loader=yaml.FullLoader)

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def get_site_template():
    info = load_json('info.json')
    template_defaults = parse_yaml(script_dir / 'template.yml')

    nav = [{'简介': info['front']}]
    nav.extend({item['title']: item['children']} for item in info['nav'])

    return info['project'] | template_defaults | {
        'extra': info['extra'],
        'nav': nav
    }

if __name__ == "__main__":
    with open('mkdocs.yml', 'w', encoding='utf-8') as file:
        yaml.dump(get_site_template(), file, allow_unicode=True, indent=4, sort_keys=False)
