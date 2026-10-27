import random

def random_item(target_list, exclude_list):
    if len(target_list) == 0:
        return None
    final_list = list(filter(lambda x: x not in exclude_list, target_list))
    if len(final_list) == 0:
        return None
    random_index = random.randint(0, len(final_list) - 1)
    return final_list[random_index]