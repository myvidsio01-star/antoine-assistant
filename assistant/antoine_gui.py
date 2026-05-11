"""
A.N.T.O.I.N.E — Interface Graphique V2.0
Style J.A.R.V.I.S — PyQt6
"""
from __future__ import annotations

import math
import os
import sys
import time
import threading

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QSizePolicy,
    QLineEdit, QSpacerItem, QProgressBar,
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QDateTime, QSize,
)
from PyQt6.QtGui import (
    QColor, QFont, QPalette, QPainter, QPen, QBrush, QCursor,
)

# ─────────────────────────────────────────────
#   PALETTE
# ─────────────────────────────────────────────

BG_MAIN   = "#09090f"
BG_CARD   = "#0d0f1a"
BG_TOPBAR = "#0a0c14"
BG_USER   = "#1a1f35"
BG_MIC    = "#1a2a35"
CYAN      = "#00c8ff"
BLUE      = "#3b82f6"
GREEN     = "#10b981"
RED       = "#ef4444"
MUTED     = "#64748b"
TEXT      = "#e2e8f0"
BORDER    = "#1a2a35"
FONT_MAIN = "Segoe UI"
FONT_MONO = "Consolas"

# ─────────────────────────────────────────────
#   HELPERS
# ─────────────────────────────────────────────

def _lbl(text="", color=TEXT, size=9, bold=False, mono=False) -> QLabel:
    w = QLabel(text)
    f = QFont(FONT_MONO if mono else FONT_MAIN, size)
    f.setBold(bold)
    w.setFont(f)
    w.setStyleSheet(f"color:{color};background:transparent;border:none;")
    return w

def _icon_btn(icon: str, tooltip="") -> QPushButton:
    b = QPushButton(icon)
    b.setToolTip(tooltip)
    b.setFixedSize(22, 22)
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    b.setStyleSheet(f"QPushButton{{background:transparent;color:{MUTED};border:none;font-size:13px;}}"
                    f"QPushButton:hover{{color:{CYAN};}}")
    return b

def _progress(color=CYAN) -> QProgressBar:
    b = QProgressBar()
    b.setRange(0, 100)
    b.setValue(0)
    b.setFixedHeight(5)
    b.setTextVisible(False)
    b.setStyleSheet(
        f"QProgressBar{{background:#1a2a35;border-radius:2px;border:none;}}"
        f"QProgressBar::chunk{{background:{color};border-radius:2px;}}")
    return b

def _round_btn(icon: str, size: int, bg: str, border: str) -> QPushButton:
    b = QPushButton(icon)
    b.setFixedSize(size, size)
    r = size // 2
    b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    b.setStyleSheet(
        f"QPushButton{{background:{bg};border:2px solid {border};"
        f"border-radius:{r}px;color:{TEXT};font-size:{size//3}px;}}"
        f"QPushButton:hover{{background:{border}33;}}"
        f"QPushButton:pressed{{background:{border}66;}}")
    return b


# ─────────────────────────────────────────────
#   ORB WIDGET (animation centrale)
# ─────────────────────────────────────────────

_ORB_STATES = {
    "idle":      {"interval": 80,  "alpha": 0.55, "speed": 0.04},
    "listening": {"interval": 50,  "alpha": 0.80, "speed": 0.10},
    "thinking":  {"interval": 35,  "alpha": 1.00, "speed": 0.18},
    "speaking":  {"interval": 40,  "alpha": 0.90, "speed": 0.14},
}

class OrbWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(260, 260)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._tick = 0.0
        self._rot  = 0.0
        self._state = "idle"
        self._dots = [0.5] * 5
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(80)

    def set_state(self, state: str):
        if state in _ORB_STATES:
            self._state = state
            self._timer.setInterval(_ORB_STATES[state]["interval"])

    def _advance(self):
        cfg = _ORB_STATES[self._state]
        self._tick += cfg["speed"]
        self._rot = (self._rot + 0.4) % 360
        for i in range(5):
            self._dots[i] = 0.5 + 0.45 * math.sin(self._tick + i * 0.7)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cfg   = _ORB_STATES[self._state]
        scale = cfg["alpha"]
        cx, cy = self.width() // 2, self.height() // 2
        c = QColor(CYAN)

        # Anneaux
        for radius, base_a, width, rot_mul in [
            (125, 0.15, 1, 1.0),
            (100, 0.25, 1, 0.7),
            (76,  0.40, 2, 0.4),
        ]:
            col = QColor(c)
            col.setAlpha(int(255 * base_a * scale))
            p.setPen(QPen(col, width))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.save()
            p.translate(cx, cy)
            p.rotate(self._rot * rot_mul)
            p.drawEllipse(-radius, -radius, radius * 2, radius * 2)
            p.restore()

        # Cercle intérieur
        r = 52
        p.setBrush(QBrush(QColor("#0a1628")))
        border_c = QColor(c); border_c.setAlpha(int(255 * 0.85 * scale))
        p.setPen(QPen(border_c, 2))
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Barres audio
        dw, dg, mh, minh = 4, 5, 20, 4
        tw = 5 * dw + 4 * dg
        sx = cx - tw // 2
        dc = QColor(c); dc.setAlpha(int(255 * 0.9 * scale))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(dc))
        for i in range(5):
            h = int(minh + (mh - minh) * self._dots[i])
            p.drawRoundedRect(sx + i * (dw + dg), cy - h // 2, dw, h, 2, 2)

        p.end()


# ─────────────────────────────────────────────
#   THREAD ASSISTANT
# ─────────────────────────────────────────────

_STATUS_MAP = {
    "Initialisation...": "idle",
    "En veille":         "idle",
    "En écoute...":      "listening",
    "Je réfléchis...":   "thinking",
    "Je parle...":       "speaking",
    "Erreur":            "idle",
}

class AssistantThread(QThread):
    message_from_user    = pyqtSignal(str)
    message_from_antoine = pyqtSignal(str)
    status_changed       = pyqtSignal(str)
    command_done         = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running        = True
        self._trigger_listen = False
        self._stop_speech    = False
        self._text_queue: list[str] = []

    def trigger_listen(self):
        self._trigger_listen = True

    def submit_text(self, text: str):
        self._text_queue.append(text)

    def stop_speech(self):
        self._stop_speech = True
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def stop(self):
        self._running = False

    def run(self):
        sys.path.insert(0, os.path.dirname(__file__))
        import antoine as core

        original_speak = core.speak

        def speak_and_emit(text: str):
            self._stop_speech = False
            self.message_from_antoine.emit(text)
            self.status_changed.emit("Je parle...")
            if not self._stop_speech:
                original_speak(text)
            self._stop_speech = False
            self.status_changed.emit("En veille")

        core.speak = speak_and_emit

        self.status_changed.emit("Initialisation...")
        core.init_tts()
        core.init_stt()
        memory = core.load_memory()
        core.speak("Antoine en ligne. Dites Hey Antoine pour me réveiller.")

        active = False
        active_since = 0.0

        while self._running:
            try:
                # Texte envoyé depuis l'input
                if self._text_queue:
                    text = self._text_queue.pop(0)
                    self.message_from_user.emit(text)
                    self.status_changed.emit("Je réfléchis...")
                    response, should_quit = core.route_command(text, memory)
                    self.command_done.emit()
                    core.speak(response)
                    if should_quit:
                        self._running = False
                    active = True
                    active_since = time.time()
                    continue

                if not active:
                    self.status_changed.emit("En veille")
                    if self._trigger_listen:
                        self._trigger_listen = False
                        active = True
                        active_since = time.time()
                        core.speak("Je vous écoute, Monsieur.")
                        continue
                    if core.listen_passive():
                        active = True
                        active_since = time.time()
                        core.speak("Je vous écoute, Monsieur.")
                    continue

                if time.time() - active_since > core.ACTIVE_TIMEOUT:
                    core.speak("Je repasse en veille, Monsieur. Dites Hey Antoine pour me réveiller.")
                    active = False
                    continue

                if self._trigger_listen:
                    self._trigger_listen = False
                    active_since = time.time()

                self.status_changed.emit("En écoute...")
                user_text = core.listen()

                if not user_text:
                    continue
                if user_text == "__not_understood__":
                    core.speak("Je n'ai pas saisi, Monsieur. Pourriez-vous répéter ?")
                    continue

                self.message_from_user.emit(user_text)
                active_since = time.time()
                self.status_changed.emit("Je réfléchis...")
                response, should_quit = core.route_command(user_text, memory)
                self.command_done.emit()
                core.speak(response)
                if should_quit:
                    self._running = False

            except Exception as exc:
                self.status_changed.emit("Erreur")
                try:
                    core.speak("Je rencontre un problème technique.")
                except Exception:
                    pass


# ─────────────────────────────────────────────
#   TOP BAR
# ─────────────────────────────────────────────

class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(45)
        self.setStyleSheet(f"background:{BG_TOPBAR};border-bottom:1px solid {BORDER};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(0)

        # Gauche — branding
        left = QHBoxLayout(); left.setSpacing(6)
        title = _lbl("A.N.T.O.I.N.E", CYAN, 11, bold=True)
        dot   = _lbl("●", GREEN, 9)
        online = _lbl("En ligne", GREEN, 8)
        left.addWidget(title); left.addWidget(dot); left.addWidget(online)
        left.addStretch()

        # Centre — horloge
        center = QHBoxLayout(); center.setSpacing(4)
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_lbl = _lbl("", TEXT, 9, mono=True)
        self._date_lbl = _lbl("", MUTED, 9)
        center.addWidget(self._time_lbl)
        center.addWidget(_lbl(" | ", MUTED, 9))
        center.addWidget(self._date_lbl)

        # Droite — météo
        right = QHBoxLayout(); right.setSpacing(8)
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._temp_lbl = _lbl("● —°C", CYAN, 9)
        right.addStretch()
        right.addWidget(self._temp_lbl)

        layout.addLayout(left, stretch=1)
        layout.addLayout(center, stretch=1)
        layout.addLayout(right, stretch=1)

        t = QTimer(self); t.timeout.connect(self._tick); t.start(1000)
        self._tick()

    def _tick(self):
        now = QDateTime.currentDateTime()
        self._time_lbl.setText(now.toString("HH:mm:ss"))
        self._date_lbl.setText(now.toString("dddd dd MMMM yyyy"))

    def update_temperature(self, temp: float, city: str):
        self._temp_lbl.setText(f"● {temp:.1f}°C  {city}")


# ─────────────────────────────────────────────
#   LEFT PANEL — cards
# ─────────────────────────────────────────────

class _Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame{{background:{BG_CARD};border:1px solid {BORDER};border-radius:8px;}}")
        self._v = QVBoxLayout(self)
        self._v.setContentsMargins(8, 8, 8, 8)
        self._v.setSpacing(6)

    def _title_row(self, text):
        row = QHBoxLayout(); row.setContentsMargins(0,0,0,0)
        row.addWidget(_lbl(text, TEXT, 9, bold=True))
        row.addStretch()
        btn = _icon_btn("↻"); row.addWidget(btn)
        self._v.addLayout(row)
        return btn

    def _bar_row(self, label):
        col = QVBoxLayout(); col.setSpacing(2)
        hdr = QHBoxLayout()
        left = _lbl(label, MUTED, 8); right = _lbl("—", TEXT, 8)
        hdr.addWidget(left); hdr.addStretch(); hdr.addWidget(right)
        bar = _progress()
        col.addLayout(hdr); col.addWidget(bar)
        self._v.addLayout(col)
        return right, bar

    def _mini_row(self, keys):
        row = QHBoxLayout(); row.setContentsMargins(0,0,0,0); row.setSpacing(0)
        vals = []
        for i, k in enumerate(keys):
            col = QVBoxLayout(); col.setSpacing(1)
            col.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            k_lbl = _lbl(k, MUTED, 7); k_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            v_lbl = _lbl("—", TEXT, 8); v_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(k_lbl); col.addWidget(v_lbl)
            row.addLayout(col, stretch=1)
            if i < len(keys) - 1:
                sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(f"color:{BORDER};"); sep.setFixedWidth(1)
                row.addWidget(sep)
            vals.append(v_lbl)
        self._v.addLayout(row)
        return vals


class SystemStatsCard(_Card):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._title_row("📊 System Stats")
        self._cpu_lbl, self._cpu_bar = self._bar_row("CPU Usage")
        self._ram_lbl, self._ram_bar = self._bar_row("RAM Usage")
        self._mini = self._mini_row(["CPU%", "Memory", "Disk"])

    def update(self, cpu, ram_pct, ram_used, ram_total, disk_used, disk_total):
        self._cpu_bar.setValue(int(cpu)); self._cpu_lbl.setText(f"{cpu:.0f}%")
        self._ram_bar.setValue(int(ram_pct)); self._ram_lbl.setText(f"{ram_used:.1f} GB")
        self._mini[0].setText(f"{cpu:.0f}%")
        self._mini[1].setText(f"{ram_used:.1f}/{ram_total:.1f}G")
        self._mini[2].setText(f"{disk_used:.0f}/{disk_total:.0f}G")
        # Couleur CPU selon charge
        cpu_color = "#ef4444" if cpu > 85 else ("#f59e0b" if cpu > 60 else "#00c8ff")
        self._cpu_bar.setStyleSheet(
            f"QProgressBar{{background:#1a2a35;border-radius:2px;border:none;}}"
            f"QProgressBar::chunk{{background:{cpu_color};border-radius:2px;}}")
        self._cpu_lbl.setStyleSheet(f"color:{cpu_color};background:transparent;")


class WeatherCard(_Card):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._title_row("🌤  Weather")
        row = QHBoxLayout(); row.setContentsMargins(0,0,0,0)
        left = QVBoxLayout(); left.setSpacing(2)
        self._temp = _lbl("—", TEXT, 20, bold=True)
        self._city = _lbl("—", MUTED, 8)
        left.addWidget(self._temp); left.addWidget(self._city)
        self._icon = _lbl("—", TEXT, 22)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addLayout(left, stretch=1); row.addWidget(self._icon)
        self._v.addLayout(row)
        self._mini = self._mini_row(["Humidity", "Wind", "Feels Like"])

    def update(self, temp, city, icon, hum, wind, feels):
        self._temp.setText(f"{temp}°C"); self._city.setText(city)
        self._icon.setText(icon)
        self._mini[0].setText(hum); self._mini[1].setText(wind); self._mini[2].setText(feels)


class UptimeCard(_Card):
    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(); row.setContentsMargins(0,0,0,0)
        row.addWidget(_lbl("⏱  System Uptime", TEXT, 9, bold=True))
        row.addStretch()
        self._uptime = _lbl("00:00:00", CYAN, 11, mono=True, bold=True)
        row.addWidget(self._uptime)
        self._v.addLayout(row)
        counts = QHBoxLayout(); counts.setContentsMargins(0,0,0,0)
        lc = QVBoxLayout(); rc = QVBoxLayout()
        lc.addWidget(_lbl("Session", MUTED, 7)); rc.addWidget(_lbl("Commands", MUTED, 7))
        self._sess = _lbl("1", TEXT, 10, bold=True)
        self._cmds = _lbl("0", TEXT, 10, bold=True)
        self._cmds.setAlignment(Qt.AlignmentFlag.AlignRight)
        lc.addWidget(self._sess); rc.addWidget(self._cmds)
        counts.addLayout(lc, stretch=1); counts.addLayout(rc, stretch=1)
        self._v.addLayout(counts)

    def update(self, uptime, commands):
        self._uptime.setText(uptime)
        self._cmds.setText(str(commands))


class BatteryCard(_Card):
    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(_lbl("⚡ Battery", TEXT, 9, bold=True))
        row.addStretch()
        self._pct_lbl = _lbl("—%", CYAN, 11, mono=True, bold=True)
        row.addWidget(self._pct_lbl)
        self._v.addLayout(row)
        self._bar = _progress(GREEN)
        self._v.addWidget(self._bar)
        self._status_lbl = _lbl("Aucune batterie", MUTED, 8)
        self._v.addWidget(self._status_lbl)

    def update(self, percent: int, plugged: bool, available: bool):
        if not available:
            self._pct_lbl.setText("N/A")
            self._status_lbl.setText("PC fixe")
            self._bar.setValue(0)
            return
        self._pct_lbl.setText(f"{percent}%")
        self._bar.setValue(percent)
        status = "En charge ⚡" if plugged else "Sur batterie"
        self._status_lbl.setText(status)
        # Couleur selon niveau
        if percent < 15 and not plugged:
            color = RED
        elif percent < 30 and not plugged:
            color = "#f59e0b"
        else:
            color = GREEN
        self._bar.setStyleSheet(
            f"QProgressBar{{background:#1a2a35;border-radius:2px;border:none;}}"
            f"QProgressBar::chunk{{background:{color};border-radius:2px;}}")
        self._pct_lbl.setStyleSheet(f"color:{color};background:transparent;border:none;")


class LeftPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(f"background:{BG_MAIN};border:none;")
        v = QVBoxLayout(self); v.setContentsMargins(4,4,4,4); v.setSpacing(4)
        self.stats   = SystemStatsCard(self)
        self.weather = WeatherCard(self)
        self.battery = BatteryCard(self)
        self.uptime  = UptimeCard(self)
        v.addWidget(self.stats); v.addWidget(self.weather)
        v.addWidget(self.battery); v.addWidget(self.uptime)
        v.addStretch()


# ─────────────────────────────────────────────
#   CENTER PANEL
# ─────────────────────────────────────────────

_STATUS_LABELS = {
    "idle":      "● En veille, Monsieur",
    "listening": "● En écoute...",
    "thinking":  "● Traitement en cours...",
    "speaking":  "● En train de parler...",
}
_STATUS_COLORS = {
    "idle": MUTED, "listening": CYAN, "thinking": BLUE, "speaking": GREEN,
}

class CenterPanel(QWidget):
    mic_clicked        = pyqtSignal()
    stop_clicked       = pyqtSignal()
    screenshot_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._orb    = OrbWidget()
        self._title  = _lbl("A.N.T.O.I.N.E", CYAN, 22, bold=True)
        self._title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        font = self._title.font()
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
        self._title.setFont(font)

        self._status = _lbl("● En veille", MUTED, 12)
        self._status.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Boutons
        self._ss_btn   = _round_btn("📷", 48, BG_CARD, CYAN)
        self._mic_btn  = _round_btn("🎤", 56, BG_CARD, CYAN)
        self._stop_btn = _round_btn("■",  48, "#1a0f0f", RED)
        self._ss_btn.clicked.connect(self.screenshot_clicked)
        self._mic_btn.clicked.connect(self.mic_clicked)
        self._stop_btn.clicked.connect(self.stop_clicked)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(18)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        btn_row.addWidget(self._ss_btn)
        btn_row.addWidget(self._mic_btn)
        btn_row.addWidget(self._stop_btn)

        orb_wrap = QWidget(); orb_wrap.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        orb_h = QHBoxLayout(orb_wrap); orb_h.setContentsMargins(0,0,0,0)
        orb_h.addStretch(); orb_h.addWidget(self._orb); orb_h.addStretch()

        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0)
        v.addStretch()
        v.addWidget(orb_wrap)
        v.addSpacing(16)
        v.addWidget(self._title, alignment=Qt.AlignmentFlag.AlignHCenter)
        v.addSpacing(8)
        v.addWidget(self._status, alignment=Qt.AlignmentFlag.AlignHCenter)
        v.addSpacing(24)
        v.addLayout(btn_row)
        v.addStretch()

    def set_status(self, status: str):
        orb_state = _STATUS_MAP.get(status, "idle")
        self._orb.set_state(orb_state)
        self._status.setText(_STATUS_LABELS.get(orb_state, f"● {status}"))
        color = _STATUS_COLORS.get(orb_state, MUTED)
        self._status.setStyleSheet(f"color:{color};background:transparent;font-size:12px;")


# ─────────────────────────────────────────────
#   RIGHT PANEL — conversation
# ─────────────────────────────────────────────

class ChatBubble(QFrame):
    def __init__(self, text: str, sender: str, parent=None):
        super().__init__(parent)
        self._sender = sender; self._text = text
        is_a = sender == "antoine"
        v = QVBoxLayout(self); v.setContentsMargins(10, 8, 10, 8); v.setSpacing(0)
        name = _lbl("A.N.T.O.I.N.E" if is_a else "Vous",
                     CYAN if is_a else MUTED, 8, bold=True)
        msg  = QLabel(text); msg.setWordWrap(True)
        msg.setFont(QFont(FONT_MAIN, 10))
        msg.setStyleSheet(f"color:{TEXT};background:transparent;")
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(name); v.addSpacing(3); v.addWidget(msg)
        if is_a:
            self.setStyleSheet(
                f"QFrame{{background:{BG_CARD};border-left:3px solid {CYAN};border-radius:8px;}}")
            self.setContentsMargins(0, 2, 24, 2)
        else:
            self.setStyleSheet(
                f"QFrame{{background:{BG_USER};border-radius:8px;}}")
            self.setContentsMargins(24, 2, 0, 2)

    @property
    def sender(self): return self._sender
    @property
    def text(self): return self._text


class RightPanel(QWidget):
    text_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bubbles: list[ChatBubble] = []
        self.setFixedWidth(285)
        self.setStyleSheet(f"background:{BG_CARD};border-left:1px solid {BORDER};")

        v = QVBoxLayout(self); v.setContentsMargins(8,8,8,8); v.setSpacing(0)
        v.addWidget(self._build_header())
        v.addSpacing(6)
        v.addWidget(self._build_scroll(), stretch=1)
        v.addSpacing(6)
        v.addWidget(self._build_input())

    def _build_header(self):
        w = QWidget(); w.setFixedHeight(36)
        h = QHBoxLayout(w); h.setContentsMargins(0,0,0,0); h.setSpacing(4)
        h.addWidget(_lbl("Conversation", TEXT, 11, bold=True))
        h.addStretch()
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._clear_btn.setStyleSheet(
            f"QPushButton{{color:{CYAN};background:transparent;border:none;font-size:11px;padding:2px 6px;}}"
            f"QPushButton:hover{{color:white;}}")
        self._export_btn = QPushButton("Export")
        self._export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._export_btn.setStyleSheet(
            f"QPushButton{{color:{MUTED};background:transparent;border:none;font-size:11px;padding:2px 6px;}}"
            f"QPushButton:hover{{color:{TEXT};}}")
        h.addWidget(self._clear_btn); h.addWidget(self._export_btn)
        self._clear_btn.clicked.connect(self.clear_messages)
        self._export_btn.clicked.connect(self.export_conversation)
        return w

    def _build_scroll(self):
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea{{background:transparent;border:none;}}"
            f"QScrollBar:vertical{{background:{BG_MAIN};width:4px;border-radius:2px;}}"
            f"QScrollBar::handle:vertical{{background:{MUTED};border-radius:2px;min-height:20px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self._container = QWidget(); self._container.setStyleSheet("background:transparent;")
        self._chat_v = QVBoxLayout(self._container)
        self._chat_v.setContentsMargins(0,0,0,0); self._chat_v.setSpacing(8)
        self._chat_v.addStretch()
        self._scroll.setWidget(self._container)
        return self._scroll

    def _build_input(self):
        w = QWidget(); w.setFixedHeight(44)
        h = QHBoxLayout(w); h.setContentsMargins(0,0,0,0); h.setSpacing(6)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Tapez un message...")
        self._input.setStyleSheet(
            f"QLineEdit{{background:{BG_MAIN};color:{TEXT};border:1px solid {BORDER};"
            f"border-radius:8px;padding:0 10px;font-family:{FONT_MAIN};font-size:11px;}}")
        self._send = QPushButton("➤")
        self._send.setFixedSize(36, 36)
        self._send.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._send.setStyleSheet(
            f"QPushButton{{background:{CYAN};color:black;border:none;border-radius:6px;"
            f"font-size:13px;font-weight:bold;}}"
            f"QPushButton:hover{{background:white;}}")
        self._send.clicked.connect(self._submit)
        self._input.returnPressed.connect(self._submit)
        h.addWidget(self._input); h.addWidget(self._send)
        return w

    def _submit(self):
        t = self._input.text().strip()
        if t:
            self._input.clear()
            self.text_submitted.emit(t)

    def add_message(self, text: str, sender: str):
        b = ChatBubble(text, sender)
        self._chat_v.insertWidget(self._chat_v.count() - 1, b)
        self._bubbles.append(b)
        QTimer.singleShot(0, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()))

    def clear_messages(self):
        for b in self._bubbles:
            self._chat_v.removeWidget(b); b.deleteLater()
        self._bubbles.clear()

    def export_conversation(self):
        if self._bubbles:
            lines = [f"{'Antoine' if b.sender=='antoine' else 'Vous'}: {b.text}"
                     for b in self._bubbles]
            QApplication.clipboard().setText("\n".join(lines))


# ─────────────────────────────────────────────
#   MAIN WINDOW
# ─────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._command_count = 0
        self.setWindowTitle("A.N.T.O.I.N.E — Assistant Vocal IA")
        self.resize(1100, 680)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(f"QMainWindow{{background:{BG_MAIN};}}")
        self._build_ui()
        self._start_thread()
        self._start_timers()
        self._load_weather_async()

    def _build_ui(self):
        central = QWidget(); central.setStyleSheet(f"background:{BG_MAIN};")
        self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        self._top    = TopBar()
        self._left   = LeftPanel()
        self._center = CenterPanel()
        self._right  = RightPanel()

        body = QHBoxLayout(); body.setContentsMargins(0,0,0,0); body.setSpacing(0)
        body.addWidget(self._left)
        body.addWidget(self._center, stretch=1)
        body.addWidget(self._right)

        root.addWidget(self._top)
        root.addLayout(body, stretch=1)

        self._right.add_message(
            "Tous mes systèmes sont opérationnels, Monsieur. Dites 'Hey Antoine' ou cliquez sur 🎤 pour commencer.", "antoine")

        self._center.mic_clicked.connect(self._on_mic)
        self._center.stop_clicked.connect(self._on_stop)
        self._center.screenshot_clicked.connect(self._on_screenshot)
        self._right.text_submitted.connect(self._on_text_input)

    def _start_thread(self):
        self._thread = AssistantThread(self)
        self._thread.message_from_user.connect(
            lambda t: self._right.add_message(t, "user"))
        self._thread.message_from_antoine.connect(
            lambda t: self._right.add_message(t, "antoine"))
        self._thread.status_changed.connect(self._on_status)
        self._thread.command_done.connect(self._on_command_done)
        self._thread.start()

    def _start_timers(self):
        # Stats système toutes les 2s
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._poll_stats)
        self._stats_timer.start(2000)
        self._poll_stats()

        # Uptime chaque seconde
        self._uptime_timer = QTimer(self)
        self._uptime_timer.timeout.connect(self._poll_uptime)
        self._uptime_timer.start(1000)

    def _poll_stats(self):
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
            import antoine as core
            s = core.get_system_stats_dict()
            d = core.get_disk_usage()
            self._left.stats.update(
                s["cpu"], s["ram_percent"], s["ram_used"], s["ram_total"],
                d["used"], d["total"])
            # Batterie
            try:
                import psutil
                bat = psutil.sensors_battery()
                if bat:
                    self._left.battery.update(int(bat.percent), bat.power_plugged, True)
                else:
                    self._left.battery.update(0, False, False)
            except Exception:
                self._left.battery.update(0, False, False)
        except Exception:
            pass

    def _poll_uptime(self):
        try:
            import antoine as core
            self._left.uptime.update(core.get_uptime(), self._command_count)
        except Exception:
            pass

    def _load_weather_async(self):
        def _fetch():
            try:
                import antoine as core
                import requests
                resp = requests.get(
                    "https://api.open-meteo.com/v1/forecast"
                    "?latitude=48.8566&longitude=2.3522"
                    "&current_weather=true&hourly=relativehumidity_2m,"
                    "apparent_temperature,windspeed_10m",
                    timeout=5)
                data = resp.json()
                cw   = data.get("current_weather", {})
                temp = cw.get("temperature", 0)
                wind = cw.get("windspeed", 0)
                city = "Paris"
                wcode = cw.get("weathercode", 0)
                icon  = "☀️" if wcode == 0 else ("⛅" if wcode < 3 else ("🌧️" if wcode > 60 else "☁️"))
                QTimer.singleShot(0, lambda: self._left.weather.update(
                    temp, city, icon, "—", f"{wind} km/h", f"{temp-2}°C"))
                QTimer.singleShot(0, lambda: self._top.update_temperature(temp, city))
            except Exception:
                pass
        threading.Thread(target=_fetch, daemon=True).start()

    def _on_status(self, status: str):
        self._center.set_status(status)

    def _on_command_done(self):
        self._command_count += 1

    def _on_mic(self):
        self._thread.trigger_listen()

    def _on_stop(self):
        self._thread.stop_speech()
        self._center.set_status("En veille")

    def _on_screenshot(self):
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            import antoine as core
            result = core.take_screenshot()
            self._right.add_message(result, "antoine")
        except Exception as e:
            self._right.add_message(f"Erreur screenshot : {e}", "antoine")

    def _on_text_input(self, text: str):
        self._thread.submit_text(text)

    def closeEvent(self, event):
        self._thread.stop()
        self._thread.quit()
        self._thread.wait(3000)
        pass
        event.accept()


# ─────────────────────────────────────────────
#   ENTRÉE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,        QColor(BG_MAIN))
    palette.setColor(QPalette.ColorRole.WindowText,    QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base,          QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.Text,          QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button,        QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText,    QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight,     QColor(CYAN))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
