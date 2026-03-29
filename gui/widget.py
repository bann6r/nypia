import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QRadioButton, QPushButton,
    QButtonGroup, QSystemTrayIcon, QMenu, QMessageBox
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QIcon, QPixmap, QPainter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG_NORMAL    = os.path.join(BASE_DIR, "nypia_logo_dark.svg")
SVG_ACTIVATED = os.path.join(BASE_DIR, "nypia_activated.svg")
ICON_DIR      = os.path.join(BASE_DIR, "icon")

try:
    sys.path.insert(0, BASE_DIR)
    from engine import NypiaHook, EVDEV_OK
    ENGINE_AVAILABLE = True
except Exception:
    ENGINE_AVAILABLE = False
    EVDEV_OK = False

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


class EngineSignalBridge(QObject):
    mode_changed = Signal(bool)


class NypiaApp(QWidget):
    def __init__(self, tray):
        super().__init__()
        self.tray = tray
        self._engine_active = False
        self._hook = None
        self._bridge = EngineSignalBridge()
        self._bridge.mode_changed.connect(self._on_mode_changed)

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
        self.svg_logo = QSvgWidget(SVG_NORMAL)
        self.svg_logo.setFixedSize(70, 70)
        logo_row.addWidget(self.svg_logo)
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
        self.rb_ctrl_shift = QRadioButton("ctrl+shift")
        self.rb_alt_z = QRadioButton("alt+z")
        self.rb_ctrl_shift.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.rb_ctrl_shift)
        group.addButton(self.rb_alt_z)
        row3.addWidget(lbl3)
        row3.addWidget(self.rb_ctrl_shift)
        row3.addWidget(self.rb_alt_z)
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
        self.btn_refs["about"].clicked.connect(self._on_about)

    def _on_mode_changed(self, viet):
        self.tray.set_viet(viet)
        self.svg_logo.load(SVG_ACTIVATED if viet else SVG_NORMAL)

    def _get_switch_key(self):
        return 'alt+z' if self.rb_alt_z.isChecked() else 'ctrl+shift'

    def _on_start(self):
        if self._engine_active:
            self.hide()
            return

        if not ENGINE_AVAILABLE:
            QMessageBox.warning(self, "error", "engine module not found\ndid you just deleted the engine?")
            return

        if not EVDEV_OK:
            QMessageBox.warning(self, "missing dependency",
                "evdev is not installed.\n\n"
                "install it:\n"
                "  pip install evdev\n"
                "    or\n"
                "  sudo dnf install python3-evdev\n\n"
                "also make sure you are in the 'input' group:\n"
                "  sudo usermod -aG input $USER\n"
                "(re-login after)")
            return

        self._hook = NypiaHook(
            on_mode_change=lambda viet: self._bridge.mode_changed.emit(viet),
            switch_key=self._get_switch_key(),
        )
        ok, err = self._hook.start()
        if not ok:
            QMessageBox.warning(self, "engine error", err)
            self._hook = None
            return

        self._engine_active = True
        self._hook.set_viet_mode(True)   # start in VN mode
        self.hide()

    def _on_exit(self):
        if self._hook:
            self._hook.stop()
        QApplication.quit()

    def _on_about(self):
        QMessageBox.about(self, "about nypia",
            "nypia v0.1\n"
            "vietnamese input method for linux\n\n"
            "github: github.com/bann6r/nypia\nsourceforge: sourceforge.net/projects/nypia\n\n"
            "© 2026 bann6r\n"
            "this program is licensed under gnu gpl v3")

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class NypiaTray(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self._viet = False
        self._app_win = None
        self.setIcon(svg_to_icon(SVG_NORMAL))
        self.setToolTip("nypia  [EN]")
        self.setVisible(True)
        self.activated.connect(self._on_click)
        self._build_menu()

    def set_app_win(self, win):
        self._app_win = win

    def _build_menu(self):
        menu = QMenu()
        self._act_toggle = menu.addAction("switch to vietnamese")
        self._act_toggle.triggered.connect(self._toggle_from_menu)
        menu.addSeparator()
        menu.addAction("setting").triggered.connect(self._show_window)
        menu.addAction("exit").triggered.connect(QApplication.quit)
        self.setContextMenu(menu)

    def set_viet(self, viet):
        self._viet = viet
        if viet:
            self.setIcon(svg_to_icon(SVG_ACTIVATED))
            self.setToolTip("nypia [vn]")
            self._act_toggle.setText("switch to english")
        else:
            self.setIcon(svg_to_icon(SVG_NORMAL))
            self.setToolTip("nypia [en]")
            self._act_toggle.setText("switch to vietnamese")

    def _toggle_from_menu(self):
        if self._app_win and self._app_win._hook:
            self._app_win._hook.toggle()

    def _show_window(self):
        if self._app_win:
            self._app_win.show()
            self._app_win.raise_()
            self._app_win.activateWindow()

    def _on_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # left click: toggle if engine running, else show settings
            if self._app_win and self._app_win._hook:
                self._app_win._hook.toggle()
            else:
                self._show_window()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            self._show_window()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = NypiaTray()
    win  = NypiaApp(tray)
    tray.set_app_win(win)
    win.show()

    sys.exit(app.exec())