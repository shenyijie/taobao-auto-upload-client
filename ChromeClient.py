import os
import time
import traceback

from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as condition
from selenium.webdriver.support.ui import WebDriverWait

import common
import constant
import stealth
from common import logger
from util import AutoUtil


# noinspection DuplicatedCode
class ChromeClient:
    def __init__(self):
        # 1. 配置浏览器打开参数
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--start-maximized')
        # chrome_options.add_argument('--headless')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        prefs = {
            'credentials_enable_service': False, 'profile.password_manager_enabled': False
        }
        chrome_options.add_experimental_option('prefs', prefs)
        chrome_options.add_argument(
            'user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"')

        # with open('stealth.min.js') as f:
        #     js = f.read()
        self.client = webdriver.Chrome(options=chrome_options, service=Service('chromedriver.exe'))
        self.client.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": stealth.CONTENT})
        self.init_login = False

    def check_slider(self):
        slider_element = self.element('//span[text()="请按住滑块，拖动到最右边"]')
        if slider_element is not None:
            logger.error("当前页面出现了滑块，尝试完成滑块拖动")
            self.client.execute_script("arguments[0].style.transform = 'translateX(100px)';", slider_element)

    def active_window(self):
        self.client.switch_to.window(self.client.current_window_handle)

    def close(self):
        try:
            self.client.quit()
        except Exception as e:
            logger.error(e)

    def element_click_by_xpath(self, element_xpath, time_out=constant.ELEMENT_TIME_OUT):
        try:
            # 等待直到元素出现
            element = WebDriverWait(self.client, time_out).until(
                condition.element_to_be_clickable((By.XPATH, element_xpath))
            )
            # 现在可以安全地与element交互，例如点击
            element.click()
        except TimeoutException:
            # 10秒内没有找到元素，抛出异常
            traceback.print_exc()
            logger.error("未能在当前页面：%s，找到元素：%s。", self.client.current_url, element_xpath)

    def element_input_by_xpath(self, element_xpath, content=None, need_check=True, time_out=constant.ELEMENT_TIME_OUT):
        try:
            # 等待直到元素出现
            element = WebDriverWait(self.client, time_out).until(
                condition.element_to_be_clickable((By.XPATH, element_xpath))
            )

            # 现在可以安全地与element交互，例如点击
            if content is not None:
                while element.get_attribute('value'):
                    element.send_keys(Keys.BACKSPACE)
                    time.sleep(0.3)
                element.send_keys(content)
                if need_check:
                    time.sleep(1)
                    while element.get_attribute('value') != str(content):
                        time.sleep(2)
                        while element.get_attribute('value'):
                            element.send_keys(Keys.BACKSPACE)
                            time.sleep(0.3)
                        element.send_keys(content)
        except TimeoutException:
            # 10秒内没有找到元素，抛出异常
            logger.error("未能在当前页面：%s，找到元素：%s。", self.client.current_url, element_xpath)
            traceback.print_exc()

    def element_select_by_xpath(self, box_path, select_xpath, target_value=None):
        try:
            # 等待直到元素出现
            WebDriverWait(self.client, 10).until(
                condition.element_to_be_clickable((By.XPATH, box_path))).click()

            # 可能存在多选项场景
            if target_value is not None and ' ' in target_value:
                matched = False
                for value_piece in target_value.split(' '):
                    strip_value = value_piece.strip()
                    if strip_value != '':
                        self.element_input_by_xpath('//div[@class="options-search"]//input', strip_value)
                        time.sleep(1)
                        if self.element_exist(f'//div[text()="{strip_value}"]'):
                            self.element_click(f'//div[text()="{strip_value}"]')
                            matched = True
                if matched:
                    logger.info(f'「{box_path}」符合多选场景，已经填入目标值：{target_value}')
                    return
            if target_value is not None:
                self.element_input_by_xpath('//div[@class="options-search"]//input', target_value)
                time.sleep(1)
            if self.element_exist(f'//div[text()="{target_value}"]'):
                self.element_click(f'//div[text()="{target_value}"]')
            else:
                logger.warning(f'{box_path}使用默认值')
                self.element_input_by_xpath('//div[@class="options-search"]//input', '')
                WebDriverWait(self.client, 10).until(
                    condition.element_to_be_clickable((By.XPATH, select_xpath))).click()
        except TimeoutException:
            # 10秒内没有找到元素，抛出异常
            traceback.print_exc()
            logger.error("未能在当前页面：%s，找到元素：%s。", self.client.current_url, box_path)

    def element(self, element_xpath, current_root=None, wait_time=10, random_move=True):
        try:
            if current_root is None:
                current_root = self.client
            target_element = WebDriverWait(current_root, wait_time).until(
                condition.presence_of_element_located((By.XPATH, element_xpath)))
            if random_move:
                AutoUtil.random_move(target_element.location['x'], target_element.location['y'])
            return target_element
        except TimeoutException:
            logger.warning(f"元素{element_xpath}未在当前页面找到")
            return None

    def element_value(self, element_xpath, wait_time=10):
        element = self.element(element_xpath, wait_time=wait_time)
        if element is None:
            return None
        else:
            return element.get_attribute('value')

    def element_exist(self, element_xpath):
        """
        不等待直接判断
        :param element_xpath: 元素位置
        :return: 是否存在
        """
        try:
            target_element = self.client.find_element(By.XPATH, element_xpath)
            AutoUtil.random_move(target_element.location['x'], target_element.location['y'])
            return True
        except NoSuchElementException:
            return False

    def element_tag(self, element_xpath, tag, current_root=None):
        element = self.element(element_xpath, current_root)
        if element is None:
            return ''
        else:
            return element.get_attribute(tag)

    def element_check(self, element_xpath):
        return not self.element(element_xpath) is None

    def element_click(self, element_xpath, wait_time=constant.ELEMENT_TIME_OUT):
        element = self.element(element_xpath, wait_time=wait_time)
        if element is not None:
            try:
                element.click()
            except ElementClickInterceptedException:
                traceback.print_exc()
                logger.error(f'元素「{element_xpath}」无法交互')
                raise Exception('页面元素预期响应')

    def element_exist_click(self, element_xpath):
        """
        元素直接判断是否存在，存在即进行点击
        :param element_xpath:
        :return:
        """
        try:
            self.client.find_element(By.XPATH, element_xpath).click()
        except NoSuchElementException:
            logger.warning(f"当前页面不存在：{element_xpath}")

    def element_hover_click(self, hover_xpath, click_xpath):
        """
        元素悬浮后提示
        :param hover_xpath: 需要悬浮的元素位置
        :param click_xpath: 需要点击的元素位置
        :return:
        """
        element = self.element(hover_xpath)
        if element is not None:
            action = ActionChains(self.client)
            action.move_to_element(element).click(element).perform()
            self.element_click(click_xpath)

    def element_hover(self, hover_xpath):
        """
        需要鼠标悬浮的元素交互
        :param hover_xpath: 需要悬浮的元素位置
        :return:
        """
        element = self.element(hover_xpath, random_move=False)
        if element is not None:
            action = ActionChains(self.client)
            action.move_to_element(element).perform()


    def element_text(self, element_xpath):
        element = self.element(element_xpath)
        if element is None:
            return ''
        else:
            return element.text

    def handle_detailed_brand(self, product_info):
        product_properties = product_info['properties']
        if self.element('//span[text()="添加材质成分"]', wait_time=2) is not None:
            if '材质成分' not in product_properties:
                raise Exception('产品页面需要先写材料成分，详细信息未未包含')
            self.element_click('//span[text()="添加材质成分"]')
            material = common.get_value_string(product_properties['材质成分'])
            self.element_select_by_xpath('//input[@placeholder="请选择材质"]', '//div[@class="options-search"]//input',
                                         material)
            percentage = common.get_value_number(product_properties['材质成分'])
            self.element_input_by_xpath('//input[@placeholder="输入含量"]', percentage)

        if self.element('//span[text()="吊牌价"]/../../../div[2]//input[@placeholder="请输入"]',
                        wait_time=2) is not None:
            if '吊牌价' not in product_properties:
                self.element_input_by_xpath('//span[text()="吊牌价"]/../../../div[2]//input[@placeholder="请输入"]',
                                            '98.9')

        # 补充处理品牌和型号没有输入的场景
        if self.element_value('//span[text()="品牌"]/../../..//input',
                        wait_time=2) == "":
            self.element_input_by_xpath('//span[text()="品牌"]/../../..//input',
                                        product_properties['品牌'], True,
                                        time_out=2)
            time.sleep(2)
        if self.element_value('//span[text()="型号"]/../../..//input',
                        wait_time=2) == "":
            if '型号' in product_properties:
                size_type = product_properties['型号']
            else:
                size_type = product_properties['品牌']
            self.element_input_by_xpath(f'//span[text()="型号"]/../../..//input',
                                        size_type, True,
                                        time_out=2)

        for element in self.client.find_elements(By.XPATH,
                                                 '//div[@class="default-items flex-item"]/div/div/div/span[2]'):
            if element.text in ['品牌', '型号', '品名', '货号']:
                continue
            elif element.text in product_properties:
                title_element = self.element(f'//span[text()="{element.text}"]/../../..//input')
                placeholder = title_element.get_attribute('placeholder')
                target_value = product_properties[element.text]
                if element.text == '产地' and target_value == '其他':
                    # 其他产地淘宝会告警
                    target_value = '中国大陆'

                if placeholder == "请选择":
                    self.element_select_by_xpath(
                        f'//span[text()="{element.text}"]/../../..//input',
                        '//div[@class="options-item"]', target_value)
                elif placeholder == "数字":
                    self.element_input_by_xpath(f'//span[text()="{element.text}"]/../../..//input',
                                                common.get_value_number(target_value), True,
                                                time_out=3)
                else:
                    self.element_input_by_xpath(f'//span[text()="{element.text}"]/../../..//input',
                                                target_value, False, time_out=3)
                if element.text == '重量' and '重量' in product_properties:
                    unit = common.get_value_string(product_properties['重量'])
                    if unit is not None and self.element_exist('//em[text()="请选单位"]'):
                        self.element_click('//em[text()="请选单位"]')
                        self.element_click(f'//span[text()="{unit}"]')
            else:
                self.element_select_by_xpath(
                    '//span[text()="' + element.text + '"]/../../..//input[@placeholder="请选择"]',
                    '//div[@class="options-item"]', None)

        if self.element_value('//span[text()="产地"]/../../..//input',
                        wait_time=2) == "":
            if '产地' in product_properties:
                location = product_properties['产地']
            else:
                location = '中国'
            self.element_input_by_xpath(f'//span[text()="产地"]/../../..//input',
                                        location, False,
                                        time_out=2)

    def handle_skus(self, product_info, price_float, quantity):
        self.element_click('//span[text()="销售信息"]')
        if self.element_exist('//h2[text()="销售信息"]/..//div[@role="tooltip"]//span'):
            self.element_click('//h2[text()="销售信息"]/..//div[@role="tooltip"]//span')

        if self.element_exist(
                '//button[contains(@class,"color-delete-icon") and not(contains(@class,"not-show-icon"))]'):
            # 部分产品会有默认的sku删除先
            self.element_click_by_xpath(
                '//button[contains(@class,"color-delete-icon") and not(contains(@class,"not-show-icon"))]', 1)

        sku_infos = product_info['sku_infos']
        sku_limit = 21
        index = 0
        old_sku_add_mode = False
        for sku_info in sku_infos:
            if sku_info['quantity'] == "0":
                continue
            if index > sku_limit:
                break
            self.element_click('//span[text()="销售信息"]')
            if self.element_exist('//span[contains(text(),"添加规格")]'):
                self.element_click('//span[contains(text(),"添加规格")]')
                old_sku_add_mode = True
                time.sleep(1)
            elif not self.element_exist('//input[@placeholder="主色(必选)" and @value=""]'):
                self.element_click(
                    '//span[text()="颜色分类"]/../../../../../div//i[contains(@class, "next-icon-alone")]')
                time.sleep(1)
            if not old_sku_add_mode:
                self.element_input_by_xpath('//input[@placeholder="主色(必选)" and @value=""]', sku_info['name'])
                time.sleep(1)
            self.element_click('//span[text()="销售信息"]')
            self.client.execute_script("arguments[0].scrollIntoView();",
                                       self.client.find_element(By.XPATH, '//span[text()="销售规格"]'))
            if old_sku_add_mode:
                self.element_input_by_xpath(f'//td[@id="{index}-skuUniqueName"]//textarea', sku_info['name'])
            self.element_input_by_xpath(f'//td[@id="{index}-skuPrice"]//input',
                                        common.get_float_price(sku_info['price'], price_float), True)
            # self.element_input_by_xpath(f'//td[@id="{index}-skuStock"]//input', quantity)
            index += 1

        # 处理尺码信息
        sizes = []
        size_key_words = ['尺码', '参考身高', '鞋码']
        for size_key_word in size_key_words:
            if self.element_exist(f'//span[contains(text(),"{size_key_word}")]'):
                self.element_click('//span[text()="销售信息"]')
                self.client.execute_script("arguments[0].scrollIntoView();",
                                           self.client.find_element(By.XPATH,
                                                                    f'//span[contains(text(),"{size_key_word}")]'))
                product_properties = product_info['properties']
                sizes_property = common.get_sizes(product_properties, size_key_word)
                if sizes_property is None:
                    # 失败让系统自动失败
                    continue
                self.element_click('//input[@placeholder="请选择尺码"]')
                for size in sizes_property.split(' '):
                    sizes.append(common.analysis_size(size))
                sizes.sort()
                break

        if len(sizes) > 0:
            for size in sizes:
                self.element_click(f'//span[@class="next-checkbox-label" and text()="{size}"]')
            self.element_click('//span[text()="确定"]')

            # 填写价格
            index = 0
            for sku_info in sku_infos:
                if sku_info['quantity'] == "0":
                    continue
                if index > sku_limit:
                    break
                price_index = index * len(sizes)
                for _ in sizes:
                    self.element_input_by_xpath(f'//td[@id="{price_index}-skuPrice"]//input',
                                                common.get_float_price(sku_info['price'], price_float), True)
                    price_index += 1
                index += 1

        # 统一填写库存信息
        self.client.execute_script("arguments[0].scrollIntoView();",
                                   self.client.find_element(By.XPATH, '//span[text()="销售规格"]'))
        self.element_input_by_xpath('//input[@id="skuStock"]', quantity)
        self.element_click('//span[text()="批量填写"]')

    def launch_chrome(self):
        try:
            self.client.get("https://www.taobao.com")
        except Exception as e:
            raise Exception('浏览器状态异常，请重新启动上传助手')
        if common.has_cookie():
            for cookie in common.get_cookie():
                if cookie['domain'] == ".taobao.com":
                    self.client.add_cookie(cookie)
            self.client.get("https://myseller.taobao.com/home.htm/QnworkbenchHome/")
            if self.element_check('//span[text()="首页"]'):
                self.init_login = True
                self.save_cookie()
            else:
                config = common.get_config()
                self.manual_login(config.get('taobao', 'account'), config.get('taobao', 'password'))
        else:
            config = common.get_config()
            self.manual_login(config.get('taobao', 'account'), config.get('taobao', 'password'))

    def open(self, url):
        self.client.get(url)

    def manual_login(self, username, password):
        self.client.get("https://login.taobao.com/member/login.jhtml")
        if self.element_exist('//button[text()="快速进入"]'):
            self.element_click('//button[text()="快速进入"]')
            if self.element_check('//span[text()="首页"]'):
                return True, f"用户：{username}，手工登录成功。"

        if self.element_exist('//span[text()="首页"]'):
            logger.warning(
                "当前已经成功登录千牛，如果需要切换账号，请手工完成账号切换动作，频繁登出登录会触发淘宝检测机制。")
            self.save_cookie()
            return True, "当前已经成功登录千牛，如果需要切换账号，请手工完成账号切换动作，频繁登出登录会触发淘宝检测机制。"

        self.element_input_by_xpath('//input[@name="fm-login-id"]', username)
        self.element_input_by_xpath('//input[@name="fm-login-password"]', password)
        self.element_click_by_xpath('//button[text()="登录"]')
        if not self.element_check('//span[text()="首页"]'):
            return False, '未能成功登录，请不要关闭页面，查看当前Chrome页面完成手工登录操作，然后重新保存验证。'
        self.save_cookie()
        self.init_login = True
        return True, f"用户：{username}，手工登录成功。"

    def save_cookie(self):
        cookies = self.client.get_cookies()
        logger.info(f"登录成功，保存最新的Cookie：{cookies}")
        common.save_cookie(cookies)

    def switch_to_frame(self, frame_num=0):
        self.client.switch_to.frame(frame_num)

    def switch_to_default(self):
        self.client.switch_to.default_content()

    def move_to_element(self, element_xpath):
        self.client.execute_script("arguments[0].scrollIntoView();",self.client.find_element(By.XPATH, element_xpath))

    def upload_product(self, product_info, strategy_config):
        current_timestamp = time.time()
        pure_id = product_info['id']
        title = product_info['title']
        logger.info(f'开始上传「{pure_id}」「{title}」，请留意上下文日志新信息')

        # 处理策略信息
        if 'words' in strategy_config:
            # 敏感词处理
            for word in strategy_config['words']:
                if word in title:
                    title = title.replace(word, '')

        if 'sku_infos' in product_info:
            new_skus = []
            price_filter = float(strategy_config['price_filter'])
            for sku_info in product_info['sku_infos']:
                quantity = int(sku_info['quantity'])
                if quantity < 1:
                    continue
                price = float(sku_info['price'])
                if price < price_filter:
                    continue
                new_skus.append(sku_info)
            if len(new_skus) == 0:
                logger.error("分析过滤后可上传的SKU为空")
                clientDB.update_product_info(pure_id, '上架失败', '分析过滤后可上传的SKU为空', current_timestamp,
                                             current_timestamp)
                return '上架失败', '分析过滤后可上传的SKU为空'
            product_info['skus_infos'] = new_skus

        pictures = product_info['pictures']
        pictures_path = {}
        main_pictures = []
        for key, value in pictures.items():
            if 'sku_' in key:
                continue
            picture_path = common.download_picture(value, pure_id, key)
            pictures_path[key] = picture_path
            if 'main_' in key:
                main_pictures.append(picture_path)

        if not self.init_login:
            self.launch_chrome()

        if not self.init_login:
            logger.error("淘宝登录未能初始化成功，请重新进行淘宝配置，若有疑问可联系供应商。")
            clientDB.update_product_info(pure_id, '上架失败', '淘宝登录信息过期，请重新淘宝配置', current_timestamp,
                                         current_timestamp)
            return '上架失败', '淘宝登录信息过期，请重新淘宝配置'

        # 1. 处理产品使用到的图片
        logger.info(f'开始处理「{pure_id}」「{title}」的商品图片')
        self.client.get('https://qn.taobao.com/home.htm/sucai-tu/home')
        # self.client.get('https://qn.taobao.com/home.htm/material-center/mine-material/sucai-tu?from=sucaitu')
        common.active_window('千牛商家工作台')
        self.element_exist_click('//a[@aria-label="关闭"]')

        self.upload_target_pictures(pure_id, pictures_path)

        # 2. 上传主图
        logger.info(f'开始上传「{pure_id}」「{title}」的商品信息')
        self.client.get('https://item.upload.taobao.com/sell/ai/category.htm?type=image')
        self.element_click('//span[text()="从图片空间"]')

        time.sleep(1)
        self.client.switch_to.frame(1)
        self.element_input_by_xpath('//input[@placeholder="请输入文件夹名称"]', pure_id)
        self.element_click(f'//span[@class="next-menu-item-text"]/span[text()="{pure_id}"]')
        self.element_click(f'//span[text()="{pure_id}"]')
        for main_picture in main_pictures:
            self.element_click(f'//div[text()="{common.get_file_base_name(main_picture)}"]/../..', 1)
        self.element_click(f'//span[contains(text(),"确定")]')
        self.client.switch_to.default_content()
        self.element_click('//span[text()="确认，下一步"]')

        # 配置品牌信息
        product_properties = product_info['properties']
        self.element("//span[text()='已上传图片']")
        if self.element_exist('//input[@placeholder="请选择"]'):
            # 有品牌信息的商品需要输入品牌和型号才能下一步
            self.element_select_by_xpath('//input[@placeholder="请选择"]', '//div[@class="options-item"]',
                                         product_properties['品牌'])
            time.sleep(1)
            if self.element_exist('//input[@placeholder="请输入"]'):
                self.element_input_by_xpath('//input[@placeholder="请输入"]', product_properties['型号'])
        elif self.element_exist('//input[@placeholder="请输入"]'):
            self.element_input_by_xpath('//input[@placeholder="请输入"]', product_properties['品牌'])
            time.sleep(1)
            if self.element_exist('//span[text()="品名"]/../../../div[2]//input[@placeholder="请输入"]'):
                self.element_input_by_xpath('//span[text()="品名"]/../../../div[2]//input[@placeholder="请输入"]',
                                            product_properties['品牌'])
            if self.element_exist('//span[text()="货号"]/../../../div[2]//input[@placeholder="请输入"]'):
                self.element_input_by_xpath('//span[text()="货号"]/../../../div[2]//input[@placeholder="请输入"]',
                                            product_properties['型号'])
            if self.element_exist('//span[text()="型号"]/../../../div[2]//input[@placeholder="请输入"]'):
                if '型号' in product_properties:
                    size_type = product_properties['型号']
                else:
                    size_type = product_properties['品牌']
                self.element_input_by_xpath('//span[text()="型号"]/../../../div[2]//input[@placeholder="请输入"]',
                                            size_type)

        self.element_click('//span[text()="确认，下一步"]')

        # 配置详细品牌信息
        self.element_input_by_xpath('//input[@placeholder="最多允许输入30个汉字（60字符）"]', title)
        self.element_click('//span[text()="类目属性"]')
        self.client.execute_script("arguments[0].scrollIntoView();",
                                   self.client.find_element(By.XPATH, '//span[text()="类目属性"]'))
        self.handle_detailed_brand(product_info)

        # 出来sku信息
        logger.info(f'开始配置「{pure_id}」「{title}」的商品sku信息')
        self.handle_skus(product_info, strategy_config['price_float'], strategy_config['quantity'])

        if 'sale' in strategy_config:
            self.client.execute_script("arguments[0].scrollIntoView();",
                                       self.client.find_element(By.XPATH, f'//span[text()="多件优惠"]'))
            time.sleep(1)
            self.element_click(f'//span[text()="{strategy_config["sale"]}"]')

        # 设置多件优惠
        if self.element_exist('//span[text()="多件优惠"]/../span[text()="*"]'):
            self.client.execute_script("arguments[0].scrollIntoView();",
                                       self.client.find_element(By.XPATH, '//span[text()="多件优惠"]'))
            time.sleep(1)
            self.element_click('//span[text()="启用"]')

        # 配置提取方式
        if self.element_exist('//span[text()="使用物流配送"]'):
            # 已经配置的不需要重复勾选
            self.element_click('//span[text()="物流服务"]')
            if self.element_tag('//span[text()="使用物流配送"]/../span/input', 'aria-checked') != 'true':
                time.sleep(1)
                self.element_click('//span[text()="使用物流配送"]')
            self.element_click('//label[text()="运费模板"]/../..//input')
            if 'express_template' in strategy_config:
                express_template = strategy_config['express_template']
            else:
                express_template = '系统模板-商家默认模板'
            self.element_click(f'//div[@class="next-menu-item-inner"]/span[text()="{express_template}"]')


        if 'express_efficiency' in strategy_config:
            self.element_click(f'//span[text()="{strategy_config["express_efficiency"]}"]')

        self.element_click('//span[text()="提交宝贝信息"]')

        if self.element('//div[text()="商品发布违规提醒"]'):
            clientDB.update_product_info(pure_id, '上架失败', self.element('//div[@class="item-shortTips"]').text,
                                         current_timestamp, current_timestamp)
            return '上架失败', self.element('//div[@class="item-shortTips"]').text

        self.element_click('//div[text()="商品提交成功"]')

        if self.element_exist('//div[text()="商品提交成功"]'):
            logger.info(f'已完成「{pure_id}」「{title}」的商品的上架')
            clientDB.update_product_info(pure_id, '上架成功', None, current_timestamp, current_timestamp)
            return '上架成功', ''
        else:
            logger.error(f'未完成「{pure_id}」「{title}」的商品的上架，')
            clientDB.update_product_info(pure_id, '上架失败', '未能成功发布，可联系服务商确认', current_timestamp,
                                         current_timestamp)
            return '上架失败', '未能成功发布，可联系服务商确认'

    def upload_target_pictures(self, product_id, pictures_path):
        product_dir = common.get_product_dir(product_id)
        if not os.path.exists(product_dir):
            raise Exception(f'商品文件为空，请重新请求')

        dir_files = os.listdir(product_dir)
        target_pictures = []
        for picture in pictures_path:
            if picture in dir_files:
                target_pictures.append(f'"{picture}"')

        if len(target_pictures) == 0:
            raise Exception(f'商品图片为空，请重新请求')

        if not self.element(f'//span[text()="{product_id}"]', wait_time=2):
            time.sleep(1)
            self.element_exist_click('//a[@aria-label="关闭"]')
            time.sleep(1)
            self.element_click('//span[text()="新建文件夹"]')
            time.sleep(1)
            self.element_input_by_xpath('//input[@aria-label="Large"]', product_id)
            time.sleep(1)
            self.element_click('//span[text()="新文件夹名称"]/../../../div[3]//span[text()="确定"]')

        time.sleep(1)
        self.element_click(f'//div/span/span[text()="{product_id}"]')
        if not self.element('//p[contains(text(),"暂无图片")]', wait_time=2):
            return
        time.sleep(1)
        self.element_click('//span[text()="上传文件"]')
        time.sleep(1)
        self.element_click('//span[text()="上传"]')
        time.sleep(1)
        common.upload_pictures(product_dir, ' '.join(target_pictures))
        time.sleep(1)
        if self.element_exist('//div[contains(text(),"上传失败")]'):
            logger.warning(f'{product_dir}存在不符合淘宝要求的图片')
        self.element_click('//span[text()="上传成功"]')
        self.element_click('//a[@aria-label="关闭"]')


if __name__ == '__main__':
    client = ChromeClient()

    while True:
        time.sleep(5)
