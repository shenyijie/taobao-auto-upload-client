# 配置视频目录和达人的关系，后续维护仅需更新此处配置，重启服务即可
FOLDER_CONFIG = {
    '玖念超有爱': '4748142768',
    '绿色的下加岭组': '4748142768'
}

NAME_FILTER = []

# 判断是否为有效达人目录
def contain_talent_name(talent_name):
    return talent_name in FOLDER_CONFIG

def get_talent_id(talent_name):
    if contain_talent_name(talent_name):
        return FOLDER_CONFIG[talent_name]
    else:
        return None