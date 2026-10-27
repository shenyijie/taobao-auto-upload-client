import json
import logging
import os
import re
import subprocess
import time
import traceback
from configparser import ConfigParser
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse, parse_qs

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_format = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

file_handler = RotatingFileHandler('info.log', maxBytes=1024 * 1024 * 15, backupCount=5, encoding='utf-8')
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)


# 公共函数
def is_empty_string(value):
    if value is None:
        return True
    elif value.strip() == '':
        return True
    else:
        return False


def list_add_no_repeat(target_list: list, element: str):
    element_strip = element.strip()
    if element_strip not in target_list:
        target_list.append(element_strip)


def save_file(file_path, content):
    file_folder = os.path.dirname(file_path)
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


# config.ini相关函数
CONFIG_FILE = 'config.ini'


def get_config():
    config = ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config


def has_config():
    return os.path.exists(CONFIG_FILE)


def save_config(config):
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


# cookie.json相关
COOKIE_JSON = './cookie.json'


def get_cookie():
    with open(COOKIE_JSON) as cookie_file:
        return json.load(cookie_file)


def has_cookie():
    return os.path.exists(COOKIE_JSON)


def save_cookie(cookie_json):
    with open(COOKIE_JSON, 'w') as cookie_file:
        json.dump(cookie_json, cookie_file)


# 商品信息相关
PRODUCT_FOLDER = './product'


def get_product_info(product_id):
    product_path = os.path.join(PRODUCT_FOLDER, product_id, f'{product_id}.json')
    if os.path.exists(product_path):
        with open(product_path, 'r', encoding='utf-8') as product_file:
            return True, json.loads(product_file.read())
    else:
        return False, '商品信息缺失，请重新请求商品信息'


def get_file_base_name(file_path):
    return os.path.basename(file_path)


def get_absolute_path(element_path):
    return os.path.abspath(element_path)


def get_url_file_name(file_url, picture_name):
    url_parse = urlparse(file_url)
    file_name = url_parse.path.split('.')[-1]
    return picture_name + '.' + file_name.split('.')[-1]


# noinspection HttpUrlsUsage
def download_picture(picture_url, product_id, picture_name):
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    product_dir: str = os.path.join(current_dir, 'product', product_id)
    if not os.path.exists(product_dir):
        os.makedirs(product_dir)
    if 'http' not in picture_url:
        picture_url = f'http:{picture_url}'
    picture_path = os.path.join(product_dir, picture_name)
    if os.path.exists(picture_path):
        return picture_path
    logger.info("正在下载图片：%s，地址为：%s", picture_url, picture_path)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0'}
    response = requests.get(picture_url, headers=headers)
    with open(picture_path, 'wb') as f:
        f.write(response.content)
    return picture_path


def get_product_dir(picture_id):
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    product_dir: str = os.path.join(current_dir, 'product', picture_id)
    return product_dir


def get_float_price(price, price_float):
    return round(float(price) * float(price_float), 2)


def execute_command(command):
    subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)


def parse_product_id(product_url):
    if 'http' not in product_url:
        return product_url

    url_parse = urlparse(product_url)
    parameters = parse_qs(url_parse.query)
    if 'id' in parameters and len(parameters['id']) > 0:
        return parameters['id'][0]
    else:
        return None


# noinspection HttpUrlsUsage
def server_post_request(api_url, request_data):
    try:
        config: ConfigParser = get_config()
        if not config.has_section('server'):
            return 403, '请完善服务配置再使用相关接口'
        server_ip = config.get('server', 'server_ip')
        server_port = config.get('server', 'server_port')
        token = config.get('server', 'token')

        request_url = f'http://{server_ip}:{server_port}/{api_url}'
        request_data.update({'token': token})
        response = requests.post(request_url, data=request_data, timeout=120)
        return response.status_code, response.text.encode('utf-8').decode('unicode-escape')
    except Exception as e:
        traceback.print_exc()
        logger.error(e)
        return 500, '服务端请求错误，请联系服务商。'


def limit_title_length(s, max_length=30):
    return s[:max_length]


def get_value_string(value):
    unit = re.search(r'(\D+)', value)
    if unit is None:
        return None
    else:
        return unit.group(1)


def get_value_number(value):
    number = re.search(r'(\d+)', value.strip())
    if number is None:
        return 1
    else:
        return int(number.group(1))


CHINESE_SIZE = ['S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'XXXXL']


def analysis_size(value):
    if value in CHINESE_SIZE:
        return value
    return get_value_number(value)

def convert_stamp_to_time(stamp):
    if stamp is None:
        return None
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stamp))

def get_sizes(product_properties, key_word):
    """
    获取产品中可能的尺码属性
    :param key_word: 界面的尺码名称
    :param product_properties: 产品属性
    :return:
    """
    if key_word in product_properties:
        return product_properties[key_word]
    for key in ['尺码', '参考身高', '鞋码']:
        if key in product_properties:
            return product_properties[key]
    else:
        return None

if __name__ == '__main__':
    print(get_value_string('100kg'))
    print(get_value_number('2双'))
    print(get_value_number('棉100%'))
    print(get_value_string('棉100%'))