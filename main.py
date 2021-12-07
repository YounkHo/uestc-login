import sys
# 从PyQt库导入QtWidget通用窗口类,基本的窗口集在PyQt5.QtWidgets模块里.
from PyQt5.QtWidgets import QApplication, QMainWindow
from window import Ui_mainWindow


if __name__ == '__main__':
    ui = Ui_mainWindow()
    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)
    w = QMainWindow()
    ui.setupUi(w, app)
    sys.exit(app.exec_())