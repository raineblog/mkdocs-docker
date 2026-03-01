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
        # e.g., build/guide.tar.zst -> build/guide.tar.zst
        matrix_list.append({"tarfile": file})

    print(json.dumps(matrix_list, separators=(',', ':')))

if __name__ == "__main__":
    generate_matrix()
