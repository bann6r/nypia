import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QRadioButton, QPushButton,
    QButtonGroup, QSystemTrayIcon
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG_NORMAL      = os.path.join(BASE_DIR, "nypia_logo_dark.svg")
SVG_ACTIVATED   = os.path.join(BASE_DIR, "nypia_activated.svg")
ICON_DIR        = os.path.join(BASE_DIR, "icon")

STYLE = """
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 13px;
}
QComboBox {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ffffff;
    min-height: 28px;
}
QComboBox:hover { border: 1px solid #555555; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #aaaaaa;
    width: 0; height: 0;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    selection-background-color: #3a3a3a;
    color: #ffffff;
    outline: none;
}
QRadioButton { spacing: 6px; color: #cccccc; }
QRadioButton::indicator {
    width: 14px; height: 14px;
    border-radius: 7px;
    border: 2px solid #555555;
    background: transparent;
}
QRadioButton::indicator:checked {
    background-color: #ffffff;
    border: 2px solid #ffffff;
}
QPushButton {
    background-color: #2e2e2e;
    border: 1px solid #3e3e3e;
    border-radius: 6px;
    padding: 8px 10px;
    color: #ffffff;
    text-align: left;
}
QPushButton:hover { background-color: #383838; border: 1px solid #555555; }
QPushButton:pressed { background-color: #252525; }
QLabel { color: #cccccc; background: transparent; }
"""

def svg_to_icon(svg_path):
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(256, 256)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class NypiaApp(QWidget):
    def __init__(self, tray):
        super().__init__()
        self.tray = tray
        self.setWindowTitle("nypia v0.1")
        self.setFixedWidth(400)
        self.setMinimumHeight(224)
        self.setStyleSheet(STYLE)
        self.setWindowIcon(svg_to_icon(SVG_NORMAL))
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 16)
        root.setSpacing(4)

        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignHCenter)
        svg = QSvgWidget(SVG_NORMAL)
        svg.setFixedSize(70, 70)
        logo_row.addWidget(svg)
        root.addLayout(logo_row)
        root.addSpacing(14)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        lbl1 = QLabel("char set:")
        lbl1.setFixedWidth(52)
        dd1 = QComboBox()
        dd1.addItem("unicode")
        row1.addWidget(lbl1)
        row1.addWidget(dd1)
        root.addLayout(row1)
        root.addSpacing(10)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        lbl2 = QLabel("method:")
        lbl2.setFixedWidth(52)
        dd2 = QComboBox()
        dd2.addItem("telex")
        row2.addWidget(lbl2)
        row2.addWidget(dd2)
        root.addLayout(row2)
        root.addSpacing(10)

        row3 = QHBoxLayout()
        row3.setAlignment(Qt.AlignHCenter)
        row3.setSpacing(10)
        lbl3 = QLabel("switch key:")
        rb1 = QRadioButton("ctrl+shift")
        rb2 = QRadioButton("alt+z")
        rb1.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(rb1)
        group.addButton(rb2)
        row3.addWidget(lbl3)
        row3.addWidget(rb1)
        row3.addWidget(rb2)
        root.addLayout(row3)
        root.addSpacing(12)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        icon_map = {
            "start":   "enable.svg",
            "exit":    "exit.svg",
            "setting": "settings.svg",
            "about":   "about.svg",
        }

        self.btn_refs = {}
        for label in ["start", "exit", "setting", "about"]:
            btn = QPushButton()
            btn.setFixedHeight(36)

            inner = QHBoxLayout(btn)
            inner.setContentsMargins(8, 0, 8, 0)
            inner.setSpacing(8)

            icon_widget = QSvgWidget(os.path.join(ICON_DIR, icon_map[label]))
            icon_widget.setFixedSize(18, 18)
            inner.addWidget(icon_widget)

            txt = QLabel(label)
            txt.setStyleSheet("color: white; background: transparent;")
            inner.addWidget(txt)
            inner.addStretch()

            btn_row.addWidget(btn)
            self.btn_refs[label] = btn

        root.addLayout(btn_row)

        self.btn_refs["start"].clicked.connect(self._on_start)
        self.btn_refs["exit"].clicked.connect(self._on_exit)

    def _on_start(self):
        self.tray.setIcon(svg_to_icon(SVG_ACTIVATED))
        self.tray.activated_state = True
        self.hide()

    def _on_exit(self):
        QApplication.quit()


class NypiaTray(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.activated_state = False
        self.setIcon(svg_to_icon(SVG_NORMAL))
        self.setToolTip("nypia")
        self.setVisible(True)
        self.activated.connect(self._on_click)

    def _on_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.activated_state:
                self.setIcon(svg_to_icon(SVG_NORMAL))
                self.activated_state = False
            else:
                self.setIcon(svg_to_icon(SVG_ACTIVATED))
                self.activated_state = True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = NypiaTray()
    win  = NypiaApp(tray)
    win.show()

    sys.exit(app.exec())