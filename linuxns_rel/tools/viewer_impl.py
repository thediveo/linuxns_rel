# Copyright 2018 Harald Albrecht
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.


from PyQt5 import QtWidgets, QtWebEngineWidgets, QtGui, QtCore
import sys


class ViewerWindow(QtWidgets.QMainWindow):
    """Saves and restores the viewer window position and geometry
    automatically."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = QtCore.QSettings("TheDiveO", "LinuxNsRel")
        if self.settings.value("geometry") is not None:
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.value("windowState") is not None:
            self.restoreState(self.settings.value("windowState"))

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Saves the current window position and geometry upon closing
        the viewer window."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)


class Viewer:

    def __init__(self, title: str, content: str) -> None:
        app = QtWidgets.QApplication(list(sys.executable))
        # noinspection PyArgumentList
        main_window = ViewerWindow()
        main_window.setObjectName('shell')
        main_window.setWindowTitle(title)
        main_window.setWindowIcon(QtGui.QIcon('favicon.png'))

        web_view = QtWebEngineWidgets.QWebEngineView(main_window)
        web_view.setObjectName('webui')
        main_window.setCentralWidget(web_view)

        web_view.setHtml(content)

        main_window.show()
        app.exec_()




if __name__ == '__main__':
    content = sys.stdin.read()
    Viewer('Namespaces', content)

