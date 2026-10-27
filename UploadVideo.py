import os
import shutil
import time

from common import logger
from util import FileUtil, AutoUtil, RandomUtil, DateUtil

TALENT_DATE = None
TALENT_COUNT_MAP = {}
# 当日已经达到上传上限的达人
TALENT_LIMIT_LIST = []

class UploadVideo:
    def __init__(self, chrome_client, personal_content, video_path):
        logger.info(f'任务已经成功响应，目标视频为：{video_path}')
        self.video_path = FileUtil.get_abs_path(video_path)
        path_split = FileUtil.split_path(video_path)
        self.video_dir = FileUtil.get_dir_path(video_path)
        self.video_name = path_split[-1]
        self.talent_name = path_split[-2]
        self.chrome_client = chrome_client
        self.talent_id = None
        self.video_title = FileUtil.get_file_title(video_path)
        self.limit = 5
        self.need_upload = True
        self.upload_success = True
        if personal_content is not None:
            if 'filter' in personal_content:
                name_filter = personal_content['filter']
                for word in name_filter:
                    self.video_title = self.video_title.replace(word, '')
            if 'limit' in personal_content:
                self.limit = personal_content['limit']
            if 'relation' in personal_content:
                relation = personal_content['relation']
                if self.video_title in relation:
                    self.need_upload = False

                if len(relation) > 0:
                    global TALENT_DATE
                    # 改成列表之后可以进行随机达人上传
                    current_day = DateUtil.get_day_of_year()
                    if TALENT_DATE != current_day:
                        TALENT_COUNT_MAP.clear()
                        TALENT_LIMIT_LIST.clear()
                        TALENT_DATE = current_day
                    self.talent_id = RandomUtil.random_item(relation, TALENT_LIMIT_LIST)

        if self.talent_id is not None:
            # 防止上传时视频被写，拷贝文件为达人的Id
            self.video_name = self.talent_id + '.mp4'
            new_video_path : str = str(os.path.join(self.video_dir, self.video_name))
            if new_video_path != self.video_path:
                if os.path.exists(new_video_path):
                    os.remove(new_video_path)
                shutil.copy(self.video_path, new_video_path)
                self.video_path = new_video_path
                logger.info(f'视频上传的实际文件为「{self.video_path}」')
            else:
                self.need_upload = False

    def check(self):
        self.upload_success = False
        if not self.need_upload:
            logger.info(f'「{self.video_path}」系统内部生成视频，跳过此次上传任务')
            return False
        if self.talent_id is None:
            logger.error('获取达人ID为空，可能原因为：达人列表为空或所有达人今天已经上传到上限')
            return False
        if not FileUtil.is_target_file(self.video_name, ".mp4"):
            logger.info(f'「{self.video_path}」非视频文件，跳过此次上传任务')
            return False

        if self.talent_id in TALENT_COUNT_MAP:
            talent_count = TALENT_COUNT_MAP[self.talent_id]
            TALENT_COUNT_MAP[self.talent_id] = talent_count + 1
            if talent_count + 1 > self.limit:
                TALENT_LIMIT_LIST.append(self.talent_id)
        else:
            TALENT_COUNT_MAP[self.talent_id] = 1
        self.upload_success = True
        return True

    def is_login(self):
        """
        检查当前是否为已经成功登录
        """
        return self.chrome_client.element_exist('//img[@alt="home"]')

    def is_success(self):
        return self.upload_success == True

    def open_upload_page(self):
        """
        打开发布上传页面
        """
        logger.info(f'「{self.video_path}」正在上传视频文件，请不要抢占鼠标')
        AutoUtil.active_window('达人管理·')
        self.chrome_client.element_click_by_xpath('//span[text()="达人管理"]')
        self.chrome_client.element_click_by_xpath('//span[text()="清除条件"]')
        self.chrome_client.element_input_by_xpath('//input[@placeholder="请输入创作者昵称/逛逛号进行搜索"]', self.talent_id)
        time.sleep(2)
        self.chrome_client.element_click_by_xpath('//span[text()="搜索"]')
        time.sleep(2)
        if not self.chrome_client.element('//span[text()="发布"]', wait_time=5):
            logger.warning(f"未能从当前页面找到发布按钮，达人id「{self.talent_id}」可能错误，此次任务跳过")
            self.upload_success = False
            return
        self.chrome_client.element_hover('//span[text()="发布"]')
        self.chrome_client.element_click_by_xpath('//*[text()="发视频"]')
        self.chrome_client.element_click_by_xpath('//*[text()="独立发布"]')
        time.sleep(2)


    def upload(self):
        """
        上传达人视频的服务逻辑
        :return:
        """
        if not self.check():
            return
        logger.info(f"任务确认，启动「{self.video_path}」上传")
        self.open_upload_page()

        if not self.is_success():
            return

        self.upload_video()
        logger.info(f"任务成功，「{self.video_path}」已经成功发布")


    def upload_video(self):
        """
        在达人上传页面进行视频上传
        """
        logger.info('正在上传视频文件')
        self.chrome_client.switch_to_frame()
        self.chrome_client.element_click_by_xpath('//span[text()="上传视频"]')
        AutoUtil.upload_file(self.video_dir, self.video_name)
        # 等待封面
        if self.chrome_client.element('//div[text()="视频可能重复发布"]', wait_time=5) is None:
            self.chrome_client.element_input_by_xpath('//input[@placeholder="加个标题让内容更吸引人"]', self.video_title, need_check=False)
            self.chrome_client.move_to_element('//div[text()="内容来源声明"]')
            self.chrome_client.element_click_by_xpath('//span[text()="立即发布"]')
            self.upload_success = True
        else:
            logger.warning(f"任务成功，「{self.video_path}」检测到重复发布，此次任务跳过")
            self.upload_success = False
        time.sleep(3)
        self.chrome_client.switch_to_default()
        logger.info('已经上传成功回到主页面')
        self.chrome_client.element_click_by_xpath('//span[text()="达人管理"]')