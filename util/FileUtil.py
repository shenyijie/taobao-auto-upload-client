import os

def exists(file_path):
    return os.path.exists(file_path)

def is_target_file(file_path, file_type):
    return file_path.endswith(file_type)

def get_file_name(file_path):
    return os.path.basename(file_path)

def get_abs_path(file_path):
    return os.path.abspath(file_path)

def get_dir_path(file_path):
    if os.path.isdir(file_path):
        return get_abs_path(file_path)
    else:
        return get_abs_path(os.path.dirname(file_path))

def get_file_suffix(file_path):
    return os.path.splitext(file_path)[1]

def get_file_title(file_path):
    file_name = get_file_name(file_path)
    return os.path.splitext(file_name)[0].strip()

def split_path(file_path):
    return file_path.split(os.path.sep)


if __name__ == '__main__':
    print(is_target_file('D:Documents\Desktop\Talent\data\大奎是只喵\给大家推荐一个真心好用的，不爱剪指甲猫咪狗狗定要试试这个.mp4', '.mp4'))