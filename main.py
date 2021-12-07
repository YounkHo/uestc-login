import sys
from PyQt5.QtWidgets import QApplication
from gui.main_widget import MainWidget

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)  # 关闭最后一个窗口不退出程序
    window = MainWidget()
    sys.exit(app.exec_())