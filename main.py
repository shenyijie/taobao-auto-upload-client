import json
import os
import sys
import time

from PyQt6.QtWidgets import QApplication, QWidget
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import Ui_Talent
from ChromeClient import ChromeClient
from UploadVideo import UploadVideo
from common import logger
from util import ChromeUtil, FileUtil, JSONUtil

SUCCESS_TALENT = set()

class FolderHandler(FileSystemEventHandler):
    def __init__(self, talent):
        self.talent = talent
        self.handled_files = []

    def on_created(self, event):
        if self.talent.in_start:
            file_path = FileUtil.get_abs_path(event.src_path)
            if file_path in self.handled_files:
                return
            logger.info(f'文件：「{file_path}」新增，触发视频上传业务')
            time.sleep(3)
            try:
                upload = UploadVideo(self.talent.chrome_client, self.talent.personal_content, file_path)
                upload.upload()
                if upload.is_success():
                    SUCCESS_TALENT.add(upload.talent_id)
                    logger.info(f'【{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}】达人「{upload.talent_id}」发布视频「{upload.video_path}」成功')
            except Exception as e:
                logger.error(f'上传日志出现错误信息为：{e}')
            self.handled_files.append(file_path)

class Talent(QWidget, Ui_Talent.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.in_edit = False
        self.in_start = False
        self.personal_file = 'config.json'
        self.refresh_ui()
        self.data_path = './data'
        self.folderLabel.setText(FileUtil.get_abs_path(self.data_path))
        self.personal_content = {}

        self.add_log("正在打开Chrome浏览器，光合平台登录后，启动任务监控")
        self.chrome_client = ChromeClient()
        self.chrome_client.open("https://mcn.guanghe.taobao.com/page/talent")

        if FileUtil.exists(self.personal_file):
            with open(self.personal_file, 'r', encoding='utf-8') as config_file:
                self.personal_content = json.load(config_file)
            if 'relation' in self.personal_content:
                self.relationEdit.clear()
                list_relation = self.personal_content['relation']
                if isinstance(list_relation, list):
                    for talent_id in list_relation:
                        self.relationEdit.appendPlainText(talent_id)
            if 'filter' in self.personal_content:
                self.filterEdit.setPlainText('\n'.join(self.personal_content['filter']))
            if 'limit' in self.personal_content:
                self.limitBox.setValue(self.personal_content['limit'])

        # 信号函数注册
        self.saveButton.clicked.connect(self.edit_config)
        self.startButton.clicked.connect(self.start_task)
        self.cleanButton.clicked.connect(self.clean_log)
        self.getButton.clicked.connect(self.get_log)

    def add_log(self, log):
        self.logEdit.appendPlainText(log)

    def clean_log(self):
        self.logEdit.clear()

    def edit_config(self):
        if self.in_edit:
            list_relation = []
            for id_input in self.relationEdit.toPlainText().split('\n'):
                list_relation.append(id_input.strip())

            if len(list_relation) == 0:
                self.logEdit.appendPlainText("达人列表为空，请正确填写达人配置信息")
                return
            self.personal_content['relation'] = list_relation
            words = []
            for word in self.filterEdit.toPlainText().split():
                words.append(word.strip())
            self.personal_content['filter'] = words
            self.personal_content['limit'] = self.limitBox.value()
            with open(self.personal_file, 'w', encoding='utf-8') as product_file:
                json.dump(self.personal_content, product_file, ensure_ascii=False, indent=4)
            self.in_edit = False
        else:
            self.in_start = False
            self.in_edit = True
        self.refresh_ui()

    def get_log(self):
        self.logEdit.clear()
        if len(SUCCESS_TALENT) == 0:
            self.logEdit.appendPlainText('此次监控成功的任务为空')
        else:
            self.logEdit.appendPlainText('成功的达人ID列表为：')
            for talent in SUCCESS_TALENT:
                self.logEdit.appendPlainText(talent)
        SUCCESS_TALENT.clear()

    def refresh_ui(self):
        if self.in_edit:
            self.startButton.setEnabled(False)
            self.saveButton.setText('保存')
            self.relationEdit.setReadOnly(False)
            self.filterEdit.setReadOnly(False)
            self.limitBox.setReadOnly(False)
        else:
            self.startButton.setEnabled(True)
            self.saveButton.setText('编辑')
            self.relationEdit.setReadOnly(True)
            self.filterEdit.setReadOnly(True)
            self.limitBox.setReadOnly(True)

        if self.in_start:
            self.startButton.setText('停止')
        else:
            self.startButton.setText('启动')

    def start_task(self):
        if self.in_start:
            self.logEdit.appendPlainText("已停止监控任务")
            self.in_start = False
        else:
            if ChromeUtil.is_login(self.chrome_client, '//img[@alt="home"]'):
                self.logEdit.appendPlainText("已经成功登录光合平台，系统会监控data目录，自动上传对应的视频")
            else:
                self.logEdit.appendPlainText("未能在当前页面检测到光合平台的页面信息，请成功登录后再点击启动监控任务")
                return
            self.in_start = True
        self.refresh_ui()


if __name__ == "__main__":
    os.system('taskkill /IM chrome.exe /F')
    os.system('taskkill /F /IM chromedriver.exe')
    time.sleep(3)

    app = QApplication(sys.argv)
    talent_upload = Talent()
    event_handler = FolderHandler(talent_upload)
    observer = Observer()
    observer.schedule(event_handler, talent_upload.data_path, recursive=True)
    observer.start()
    talent_upload.show()
    sys.exit(app.exec())
