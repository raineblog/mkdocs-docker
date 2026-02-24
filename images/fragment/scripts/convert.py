import pypandoc
import os

def auto_convert_file(extra_args, filters):
    # output = pypandoc.convert_file(
    #     filename,
    #     to='commonmark_x',
    #     format='html+native_divs',
    #     extra_args=extra_args,
    #     filters=filters
    # )

    for root, _, files in os.walk('site'):
        for file in files:
            if file.endswith('.html'):
                input_path = os.path.join(root, file)
                output_path = os.path.splitext(input_path)[0] + '.md'
                pypandoc.convert_file(
                    input_path,
                    to='commonmark_x',
                    format='html+native_divs',
                    outputfile=output_path,
                    extra_args=extra_args,
                    filters=filters
                )

def main():
    filters = []
    pdoc_args = ['--wrap=none', '--citeproc']
    auto_convert_file(pdoc_args, filters)

if __name__ == "__main__":
    main()
