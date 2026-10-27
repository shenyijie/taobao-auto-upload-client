import time

import autoit
import random

from common import logger

def active_window(window_name):
    """
    激活指定名称的窗口
    :param window_name:
    """
    autoit.win_wait(window_name)
    autoit.win_activate(window_name)

def move_limit(position):
    """
    :param position: 输入的位置
    :return: 限定调整后的位置
    """
    if position < 200:
        return 200
    elif position > 1600:
        return 1600
    else:
        return position


def random_move(x, y):
    """
    根据所需要移动的位置，将鼠标焦点移动目标附近随机位置
    :param x:
    :param y:
    """
    autoit.mouse_move(move_limit(x), move_limit(y), random.randint(50, 150))


def upload_file(file_dir, file_base, window_name='打开'):
    logger.info(f"正在上传文件：{file_dir}，目标值为：{file_base}")
    time.sleep(3)
    active_window(window_name)
    time.sleep(1)
    autoit.control_click(window_name, "ToolbarWindow323", x=10, y=10)
    time.sleep(1)
    autoit.control_set_text(window_name, "Edit2", file_dir)
    autoit.control_click(window_name, "ToolbarWindow324")
    time.sleep(1)
    autoit.control_set_text(window_name, "Edit1", file_base)
    time.sleep(1)
    autoit.control_click(window_name, "Button1")