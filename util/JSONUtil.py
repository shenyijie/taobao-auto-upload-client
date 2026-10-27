import json


def load_json_dict(json_str):
    try:
        json_object = json.loads(json_str)
        if isinstance(json_object, dict):
            return json_object
        else:
            return None
    except ValueError:  # 更准确的异常是 json.JSONDecodeError，但在Python 3.5及之前版本中没有这个异常
        return None

def format_json(json_str):
    return json.dumps(json_str, ensure_ascii=False, indent=4)