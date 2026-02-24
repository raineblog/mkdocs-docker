import pypandoc
import os
import re
import urllib.parse

def fix_paths(content):
    # 处理 Markdown 图片和链接: ![alt](../path) 或 [text](../../path)
    def md_callback(match):
        prefix = match.group(1)
        path = match.group(2)
        # 修复路径：将开头的 ../ 替换为 ./
        path = re.sub(r'^(\.\./)+', './', path)
        # 解码中文文件名
        return prefix + urllib.parse.unquote(path) + ')'

    content = re.sub(r'(!?\[.*?\]\()([^)]+)\)', md_callback, content)
    
    # 处理 HTML 标签: <img src="../path"> 或 <a href="../../path">
    def html_callback(match):
        prefix = match.group(1)
        path = match.group(2)
        # 修复路径：将开头的 ../ 替换为 ./
        path = re.sub(r'^(\.\./)+', './', path)
        # 解码中文文件名
        return prefix + urllib.parse.unquote(path) + '"'

    content = re.sub(r'(src="|href=")([^"]+)"', html_callback, content)
    
    return content

def auto_convert_file(extra_args, filters):
    for root, _, files in os.walk('site'):
        for file in files:
            if file.endswith('.html'):
                input_path = os.path.join(root, file)
                
                # 确定输出路径: 某个文件夹/xxx/index.html -> 某个文件夹/xxx.md
                rel_path = os.path.relpath(input_path, 'site')
                dirname = os.path.dirname(rel_path)
                
                if dirname == "":
                    # 根目录下的 index.html -> index.md
                    output_name = os.path.splitext(file)[0] + '.md'
                    output_path = os.path.join('site', output_name)
                else:
                    # 子目录下的 index.html -> 子目录名.md
                    # 例如: site/posts/index.html -> site/posts.md
                    output_path = os.path.join('site', dirname + '.md')

                # 先转换为字符串，进行处理后再写入文件
                output = pypandoc.convert_file(
                    input_path,
                    to='commonmark_x+fenced_divs',
                    format='html+raw_html+native_divs',
                    extra_args=extra_args,
                    filters=filters
                )
                
                # 修复路径
                fixed_content = fix_paths(output)
                
                # 写入文件
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

def main():
    # 动态获取当前脚本所在目录，确保在 Docker 或本地运行都能找到过滤器
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lua_filter_path = os.path.join(script_dir, 'html-cleanup.lua')
    
    filters = [lua_filter_path]
    pdoc_args = ['--wrap=none', '--standalone', '--indent=4']
    auto_convert_file(pdoc_args, filters)

if __name__ == "__main__":
    main()
