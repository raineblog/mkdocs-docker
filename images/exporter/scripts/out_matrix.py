import os
import json
import glob


def generate_matrix():
    tar_files = glob.glob("build/*.tar.zst")
    if not tar_files:
        print("[]")
        return

    matrix_list = []
    for file in tar_files:
        # 仅传递文件名，不包含 build/ 前缀，方便二级 Job 直接读取根目录资源
        matrix_list.append({"tarfile": os.path.basename(file)})

    print(json.dumps(matrix_list, separators=(",", ":")))


if __name__ == "__main__":
    generate_matrix()
