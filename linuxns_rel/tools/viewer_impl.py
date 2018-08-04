"""A "qute" simple SVG viewer, allowing pan and zoom, as well as saving
the displayed SVG image to a file.

The rationales for this SVG viewer are twofold: first, it is much
lighter than an embedded chromium web engine. Second, it allows to us
to read the SVG image to be displayed from a pipe, without having to
resort to temporary files in the filesystem, over which we have no
lifecycle control when using a web browser. Third, we cannot "pipe"
SVG content anymore using "data:" URLs into web browsers anymore for
security reasons, as top-level navigational "data:" URLs have now been
blocked.
"""

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


from PyQt5 import QtWidgets, QtSvg, QtCore, QtGui
from PyQt5.QtWidgets import (QFileDialog, QGraphicsItem, QGraphicsView,
                             QGraphicsScene, QMainWindow, QMessageBox,
                             QWidget)
from PyQt5.QtGui import QCloseEvent, QKeyEvent, QWheelEvent
import sys
from os import path


class SvgView(QGraphicsView):
    """SVG content viewer, which allows the user to zoom in/out using
    the mouse wheel, and to drag or scroll the image around.
    """

    # noinspection PyShadowingNames
    def __init__(self, content: str, parent: QWidget=None):
        """Creates a new SVG viewer with the given SVG content.

        :param content: the SVG content to show.
        :param parent: optional parent widget, defaults to None.
        """
        super().__init__(parent)

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

    def zoom(self, factor: float):
        """Zooms in or out by a factor, limiting zooming to the range
        between 0.1x and 10x.

        :param factor: >1.0 to zoom in, and <1.0 to zoom out.
        """
        current_zoom = self.transform().m11()
        if factor < 1 and current_zoom > 0.1 \
                or factor >= 1 and current_zoom < 10:
            self.scale(factor, factor)

    def keyPressEvent(self, event: QKeyEvent):
        """Handles keys "+" to zoom in, "-" to zoom out, and "1" to
        reset the zoom back to 1x.
        """
        key = event.key()
        if key == QtCore.Qt.Key_Plus:
            self.zoom(1.2)
            event.accept()
        elif key == QtCore.Qt.Key_Minus:
            self.zoom(1/1.2)
            event.accept()
        elif key == QtCore.Qt.Key_1:
            self.reset_zoom()
            event.accept()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        """Zooms in or out the SVG image, depending on which direction
        the mouse wheel is being spun, and how far since the last
        wheel spin event.
        """
        factor = pow(1.2, event.angleDelta().y() / 240.0)
        self.zoom(factor)
        event.accept()


# noinspection PyShadowingNames
class SvgViewerMainWindow(QMainWindow):
    """Saves and restores the viewer window position and geometry
    automatically."""

    def __init__(self, content: str, title: str='', parent=None) \
            -> None:
        # noinspection PyArgumentList
        super().__init__(parent)

        self.content = content

        self.settings = QtCore.QSettings("TheDiveO", "LinuxNsRel")
        if self.settings.value("geometry") is not None:
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.value("windowState") is not None:
            self.restoreState(self.settings.value("windowState"))

        self.view = SvgView(content)
        self.setCentralWidget(self.view)
        self.setWindowTitle(
            title if title is not None else 'SVG Viewer')
        self.setWindowIcon(QtGui.QIcon(
            path.dirname(path.abspath(__file__)) + '/linuxnsrel.svg'))

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handles "q" key to close (and exit) the SVG viewer.
        """
        key = event.key()
        if key == QtCore.Qt.Key_Q:
            event.accept()
            self.close()
        elif key == QtCore.Qt.Key_S:
            event.accept()
            self.save()
        elif key == QtCore.Qt.Key_H:
            event.accept()
            QMessageBox.information(
                self,
                'SVG Viewer Help',
                'Mouse:\n'
                '  wheel: zoom in/out\n'
                'Keys:\n'
                '  + or -: zoom in/out respectively\n'
                '  1: reset zoom to 1x\n'
                '  s: save SVG to file\n'
                '  q: quit viewer\n'
                '  h: show this help',
                QMessageBox.Ok, QMessageBox.Ok)
        else:
            super().keyPressEvent(event)

    def save(self) -> None:
        """Shows a file save dialog and then saves the SVG image to the
        user-specified file.
        """
        sd = QFileDialog()
        sd.setDefaultSuffix('svg')
        sd.setAcceptMode(QFileDialog.AcceptSave)
        sd.setNameFilters(['SVG (*.svg)', 'All (*)'])
        if sd.exec_() == QFileDialog.Accepted:
            with open(sd.selectedFiles()[0], 'w') as f:
                f.write(self.content)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Saves the current window position and geometry upon closing
        the viewer window.
        """
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        super().closeEvent(event)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--title', default='SVG Viewer')
    my_args, qt_args = parser.parse_known_args()

    content = sys.stdin.read()

    app = QtWidgets.QApplication(sys.argv[:1] + qt_args)
    mw = SvgViewerMainWindow(content, title=my_args.title)
    mw.show()
    sys.exit(app.exec())
