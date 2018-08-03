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


from PyQt5 import QtWidgets, QtGui, QtSvg, QtCore
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsView, QGraphicsScene, QWidget
import sys


class SvgView(QGraphicsView):
    """."""

    def __init__(self, content: str, parent=None):
        super().__init__(parent)

        self.setViewport(QWidget())

        self.setScene(QGraphicsScene(self))
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        svg_renderer = QtSvg.QSvgRenderer(content.encode('utf-8'))
        svg_item = QtSvg.QGraphicsSvgItem()
        svg_item.setSharedRenderer(svg_renderer)
        svg_item.setFlags(QGraphicsItem.ItemClipsToShape)
        svg_item.setCacheMode(QGraphicsItem.NoCache)
        svg_item.setZValue(0)

        scene = self.scene()
        scene.clear()
        self.resetTransform()
        scene.addItem(svg_item)
        scene.setSceneRect(svg_item.boundingRect())

    def reset_zoom(self):
        """Resets the zoom to 1.0."""
        self.resetTransform()

    def wheelEvent(self, event: QtGui.QWheelEvent):
        """Zooms in or out the SVG image, depending on which direction
        the mouse wheel is being spun, and how far since the last
        wheel spin event. Limits zooming to the range of 0.1x up to 10x.
        """
        current_zoom = self.transform().m11()
        print('current zoom', current_zoom)
        sys.stdout.flush()
        factor = pow(1.2, event.angleDelta().y() / 240.0)
        if factor < 1 and current_zoom > 0.1 \
                or factor >= 1 and current_zoom < 10:
            self.scale(factor, factor)
        event.accept()


class SvgViewerMainWindow(QtWidgets.QMainWindow):
    """Saves and restores the viewer window position and geometry
    automatically."""

    def __init__(self, content: str, parent=None) -> None:
        # noinspection PyArgumentList
        super().__init__(parent)

        self.settings = QtCore.QSettings("TheDiveO", "LinuxNsRel")
        if self.settings.value("geometry") is not None:
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.value("windowState") is not None:
            self.restoreState(self.settings.value("windowState"))

        self.view = SvgView(content)
        self.setCentralWidget(self.view)
        self.setWindowTitle('SVG Viewer')

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Saves the current window position and geometry upon closing
        the viewer window."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)


if __name__ == '__main__':
    content = sys.stdin.read()
    app = QtWidgets.QApplication(sys.argv)
    mw = SvgViewerMainWindow(content)
    mw.show()
    sys.exit(app.exec())
