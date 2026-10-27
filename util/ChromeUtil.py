
def is_login(chrome_client, target_xpath):
    return chrome_client.element_exist(target_xpath)
