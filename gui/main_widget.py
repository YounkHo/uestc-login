import time
import json
import os.path
import threading
import logging
import sys

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QAction, QMenu, QSystemTrayIcon, QApplication, QMessageBox
from gui.window import Ui_mainWindow
import assets.resource

from login.login import Login


class MainWidget(QMainWindow, Ui_mainWindow):
    def __init__(self, parent=None):
        super(MainWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('电子科技大学自动登录')
        self.setWindowIcon(QIcon(':/img/logo.ico'))
        self.setFixedSize(self.width(), self.height())

        self.openAction = QAction("启动", self)
        self.openAction.setIcon(QApplication.style().standardIcon(QApplication.style().SP_DialogApplyButton))
        self.configAction = QAction("配置", self)
        self.configAction.setIcon(QApplication.style().standardIcon(QApplication.style().SP_FileDialogEnd))
        self.logAction = QAction("日志", self)
        self.logAction.setIcon(QApplication.style().standardIcon(QApplication.style().SP_FileDialogDetailedView))
        self.aboutAction = QAction("关于", self)
        self.aboutAction.setIcon(QApplication.style().standardIcon(QApplication.style().SP_FileDialogInfoView))
        self.quitAction = QAction("退出", self)
        self.quitAction.setIcon(QApplication.style().standardIcon(QApplication.style().SP_BrowserStop))

        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.openAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.configAction)
        self.trayIconMenu.addAction(self.logAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.aboutAction)
        self.trayIconMenu.addAction(self.quitAction)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(QIcon(":/img/logo.ico"))
        self.trayIcon.setToolTip("成电网络")
        self.trayIcon.show()

        self.login = None
        self.launched = False #是否循环登录的标志位，设为否不自动循环登录
        self.running = True #子线程运行的标志位。设为否子线程强自退出，
        self.loginThread = None

        self.initLog()
        self.initConnect()
        self.initLogin()
        self.loginThread = threading.Thread(target=self.run, name='login_thread')
        self.loginThread.start()

    def initLog(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # set two handlers
        log_dir = 'log/'
        log_file = "{}.log".format(__name__)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        # rm_file(log_file)
        fileHandler = logging.FileHandler(os.path.join(log_dir, log_file), mode='w')
        fileHandler.setLevel(logging.INFO)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.DEBUG)

        # set formatter
        formatter = logging.Formatter('[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        consoleHandler.setFormatter(formatter)
        fileHandler.setFormatter(formatter)

        # add
        self.logger.addHandler(fileHandler)
        self.logger.addHandler(consoleHandler)
        self.logger.debug("App Start")

    def set_launched_ui(self, open):
        if open:
            self.logger.warning("Launch Thread Start: start login and online status check")
            self.openAction.setIcon(QApplication.style().standardIcon(QApplication.style().SP_DialogCancelButton))
            self.openAction.setText("关闭")
            if self.loginThread and not self.loginThread.is_alive(): # 由于休眠导致的线程死亡
                self.logger.warning("Due to unknown reason, Thread has dead, Restarted now!")
                if self.loginThread: self.loginThread.start()
                else: self.initLogin()
        else:
            self.logger.warning("Launch Thread Stop")
            self.openAction.setIcon(QApplication.style().standardIcon(QApplication.style().SP_DialogApplyButton))
            self.openAction.setText("启动")
        self.launched = not self.launched

    def initLogin(self):
        if not os.path.exists('config.json'):
            self.configApp()
            return
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
            if config['position'] == 0:
                self.login = Login(config['username'], config['password'])
                self.logger.debug("Current Location: 主楼")
            else:
                self.login = Login(config['username'], config['password'], ac_id="3", domain="@cmcc", base_auth_url="http://10.253.0.237/")
                self.logger.debug("Current Location: 寝室（硕丰）")
            self.set_launched_ui(True)

    def initConnect(self):
        self.openAction.triggered.connect(self.launchApp)
        self.configAction.triggered.connect(self.configApp)
        self.quitAction.triggered.connect(self.quitApp)
        self.aboutAction.triggered.connect(self.aboutApp)
        self.logAction.triggered.connect(self.logShow)

        self.ok.clicked.connect(self.saveConfig)
        self.exit.clicked.connect(self.quitApp)

    def logShow(self):
        log_dir = 'log/'
        if os.path.exists(log_dir):
            self.logger.debug("Open Log File!")
            os.startfile(os.path.join(os.getcwd(), log_dir))
        else:
            self.logger.critical("Log File Not Found!")
            QMessageBox.critical(self, "FileNotFound", "未找到有效日志文件目录", QMessageBox.Yes)

    def aboutApp(self):
        self.logger.info("本程序仅供学习，严禁用于非法用途！更多详情请访问github！")
        QMessageBox.about(self, "说明", "本程序仅供学习，严禁用于非法用途！更多详情请访问github！")

    def saveConfig(self):
        if self.username.text().strip() == '' or self.password.text().strip() == '':
            QMessageBox.warning(self, "配置错误警告", "用户名或密码不能为空", QMessageBox.Yes)
            return

        with open('config.json', 'w', encoding="UTF-8") as f:
            config = {
                "username": self.username.text().strip(),
                "password": self.password.text().strip(),
                "position": 0 if self.mainbuilding.isChecked() else 1
            }
            json.dump(config, f)
            if self.login:
                self.login.update_username(self.username.text().strip())
                self.login.password = self.password.text().strip()
                self.login.tried = 0
                self.login.status = 0
            elif config['position'] == 0:
                self.login = Login(config['username'], config['password'])
            else:
                self.login = Login(config['username'], config['password'], ac_id="3", domain="@cmcc", base_auth_url='http://10.253.0.237/')

            self.hide()
            self.trayIcon.showMessage("用户配置已更新", "用户配置已成功更新", icon=1)
            self.logger.warning("User Config is Updated")

    def quitApp(self):
        self.logger.warning("App quit")
        self.running = False
        self.loginThread.join()
        QCoreApplication.quit()
        sys.exit(0)

    def configApp(self):
        if os.path.exists('config.json'):
            with open("config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.username.setText(config['username'])
                self.password.setText(config['password'])
                if config['position'] == 0:
                    self.mainbuilding.setChecked(True)
                else:
                    self.dorm.setChecked(True)
            self.show()
        else:
            self.show()

    def launchApp(self):
        if self.login is None:
            QMessageBox.critical(self, "配置为空", "请通过托盘配置登录信息", QMessageBox.Yes)
            self.configApp()
            return
        self.set_launched_ui(not self.launched)
        self.logger.warning("Change Launch Status: {}".format(str(self.launched)))
        self.logger.warning("Thread Status: {}".format(str(self.loginThread.is_alive())))

    def run(self):
        while self.running:
            if self.launched:
                try:
                    content = self.login.check_status()
                except Exception as err:
                    self.logger.warning("When Check Status Exception")
                    self.logger.critical(err)
                except SystemExit as err:
                    self.logger.warning("When Check Status System Exit Error")
                    self.logger.critical(err)
                self.logger.info(content)
                if 'res' not in content and "error" in content and content['error'] == 'ok' and self.login.status != 0: #我也记不得这段代码当时是判断啥场景了，操！
                    self.trayIcon.showMessage(content['user_name'] + ' 网络正常', "当前IP："+content['online_ip'], icon=1)
                    self.trayIcon.setToolTip("成电网络\n\n当前用户：" + content['user_name'] + ' \n当前IP：' + content['online_ip'] + ' \n上线时间：\n' + time.strftime('%m-%d %H:%M', time.localtime(content['add_time'])))
                    self.logger.warning(content['user_name'] + ' 网络正常 '+ "；当前IP："+content['online_ip'])
                    self.login.status = 0
                elif 'res' in content and content['res'] == 'not_online_error':
                    self.trayIcon.setToolTip("成电网络\n\n" + self.login.username.replace(self.login.domain, '') + ' 已离线')
                    if self.login.status < 2:
                        self.trayIcon.showMessage(self.login.username.replace(self.login.domain, '') + ' 已离线', "登出IP："+content['online_ip'], icon=2)
                        self.logger.critical(content)
                        self.login.status += 1
                    try:
                        result = self.login.login()
                    except Exception as err:
                        self.logger.warning("When Login Exception")
                        self.logger.critical(err)
                    except SystemExit as err:
                        self.logger.warning("When Login System Exit Error")
                        self.logger.critical(err)
                    self.logger.info(result)
                    if "error_msg" in result and "res" in result and result['error'] == "login_error" and self.login.tried <= 2:
                        self.trayIcon.showMessage(self.login.username.replace(self.login.domain, '') + ' 登录失败', result['error_msg'], icon=2)
                        self.logger.critical("Login Res："+result['error_msg'])
                        self.login.tried += 1
                        self.login.status = 1
                    elif "ploy_msg" in result and "res" in result and result['ploy_msg'] == "E0000: Login is successful.":
                        self.trayIcon.showMessage(self.login.username.replace(self.login.domain, '') + ' 登录成功', result['ploy_msg'], icon=1)
                        self.trayIcon.setToolTip("成电网络\n\n当前用户：" + self.login.username.replace(self.login.domain, '') + ' \n当前IP：' + self.login.ip + ' \n上线时间：\n' + time.strftime('%m-%d %H:%M', time.localtime()))
                        self.logger.warning("Login Res："+result['res']+"； Login IP："+self.login.ip)
                        self.login.tried = 0
                        self.login.status = 0
            else:
                self.logger.warning("Not Auto Login Now.")
            time.sleep(10)
