"""
A.N.T.O.I.N.E — GUI V1.1
Interface graphique PyQt6 pour l'assistant vocal A.N.T.O.I.N.E.
"""

import sys
import os
import time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation,
    QEasingCurve, QSize,
)
from PyQt6.QtGui import QFont, QColor, QPalette, QCursor

# ─────────────────────────────────────────────
#   PALETTE & CONSTANTES DE STYLE
# ─────────────────────────────────────────────

BG_MAIN    = "#09090f"
BG_CARD    = "#0d0f1a"
BG_USER    = "#1a1f35"
BG_TOPBAR  = "#0a0c14"
BG_MIC     = "#1a2a35"

CYAN       = "#00c8ff"
BLUE       = "#3b82f6"
GREEN      = "#10b981"
MUTED      = "#64748b"
TEXT       = "#e2e8f0"
BORDER     = "#1a2a35"

FONT_MAIN  = "Segoe UI"
FONT_CODE  = "Consolas"


# ─────────────────────────────────────────────
#   THREAD ASSISTANT
# ─────────────────────────────────────────────

class AssistantThread(QThread):
    """
    Exécute la boucle principale d'A.N.T.O.I.N.E dans un QThread dédié.
    Communique avec l'UI uniquement via des signaux Qt.
    """

    message_from_user    = pyqtSignal(str)
    message_from_antoine = pyqtSignal(str)
    status_changed       = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running        = True
        self._trigger_listen = False
        self._stop_speech    = False

    def trigger_listen(self):
        """Appel externe pour forcer une écoute immédiate."""
        self._trigger_listen = True

    def stop_speech(self):
        """Interrompt la parole en cours et annule l'action actuelle."""
        self._stop_speech = True
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def stop(self):
        """Arrêt propre du thread."""
        self._running = False

    def run(self):
        """Boucle principale adaptée pour le GUI."""
        sys.path.insert(0, os.path.dirname(__file__))
        import antoine as core  # noqa: PLC0415  (import local intentionnel)

        # ── Redirection de core.speak ──
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

        # ── Initialisation des moteurs ──
        self.status_changed.emit("Initialisation...")
        core.init_tts()
        core.init_stt()
        memory = core.load_memory()

        core.speak("Antoine en ligne. Dites 'Hey Antoine' pour me réveiller.")

        active       = False
        active_since = 0.0

        while self._running:
            try:
                # ─── Mode veille ───
                if not active:
                    self.status_changed.emit("En veille")

                    # Activation manuelle via bouton MIC
                    if self._trigger_listen:
                        self._trigger_listen = False
                        active       = True
                        active_since = time.time()
                        core.speak("Je vous écoute.")
                        continue

                    # Détection passive du wake word
                    if core.listen_passive():
                        active       = True
                        active_since = time.time()
                        core.speak("Je vous écoute.")
                    continue

                # ─── Timeout d'activité ───
                if time.time() - active_since > core.ACTIVE_TIMEOUT:
                    core.speak("Je repasse en veille. Dites 'Hey Antoine' pour me réveiller.")
                    active = False
                    continue

                # ─── Bouton MIC en mode actif : forcer une nouvelle écoute ───
                if self._trigger_listen:
                    self._trigger_listen = False
                    active_since = time.time()

                # ─── Écoute et traitement ───
                self.status_changed.emit("En écoute...")
                user_text = core.listen()

                if not user_text:
                    continue

                if user_text == "__not_understood__":
                    core.speak("Je n'ai pas compris. Pouvez-vous répéter ?")
                    continue

                self.message_from_user.emit(user_text)
                active_since = time.time()

                self.status_changed.emit("Je réfléchis...")
                response, should_quit = core.route_command(user_text, memory)
                core.speak(response)

                if should_quit:
                    self._running = False

            except Exception as exc:
                self.status_changed.emit("Erreur")
                core.speak(f"Je rencontre un problème technique : {exc}")


# ─────────────────────────────────────────────
#   WIDGET BULLE DE CHAT
# ─────────────────────────────────────────────

class ChatBubble(QFrame):
    """
    Bulle de conversation pour Antoine (gauche, cyan) ou l'utilisateur (droite, gris).
    """

    def __init__(self, text: str, sender: str, parent=None):
        super().__init__(parent)
        self._build(text, sender)

    def _build(self, text: str, sender: str):
        is_antoine = (sender == "antoine")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 4, 8, 4)
        outer.setSpacing(0)

        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Nom de l'émetteur
        name_label = QLabel("A.N.T.O.I.N.E" if is_antoine else "Vous")
        name_label.setFont(QFont(FONT_MAIN, 8, QFont.Weight.Bold))
        name_color = CYAN if is_antoine else MUTED
        name_label.setStyleSheet(f"color: {name_color}; background: transparent;")
        layout.addWidget(name_label)

        # Texte du message
        msg_label = QLabel(text)
        msg_label.setFont(QFont(FONT_MAIN, 10))
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {TEXT}; background: transparent;")
        msg_label.setMaximumWidth(500)
        layout.addWidget(msg_label)

        # Style de la bulle
        if is_antoine:
            container.setStyleSheet(
                f"background: {BG_CARD}; border-radius: 10px;"
                f"border-left: 3px solid {CYAN};"
            )
        else:
            container.setStyleSheet(
                f"background: {BG_USER}; border-radius: 10px;"
                f"border: 1px solid {BORDER};"
            )

        if is_antoine:
            outer.addWidget(container, alignment=Qt.AlignmentFlag.AlignLeft)
            outer.addStretch()
        else:
            outer.addStretch()
            outer.addWidget(container, alignment=Qt.AlignmentFlag.AlignRight)

        self.setStyleSheet("background: transparent; border: none;")


# ─────────────────────────────────────────────
#   ZONE DE CHAT DÉFILABLE
# ─────────────────────────────────────────────

class ChatArea(QScrollArea):
    """Zone de chat avec défilement automatique vers le bas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._container = QWidget()
        self._layout    = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.setSpacing(2)
        self._layout.setContentsMargins(0, 8, 0, 8)

        self.setWidget(self._container)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            f"QScrollArea {{ background: {BG_MAIN}; border: none; }}"
            f"QWidget {{ background: {BG_MAIN}; }}"
            f"QScrollBar:vertical {{"
            f"  background: {BG_CARD}; width: 6px; border-radius: 3px;"
            f"}}"
            f"QScrollBar::handle:vertical {{"
            f"  background: {BORDER}; border-radius: 3px;"
            f"}}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{"
            f"  height: 0px;"
            f"}}"
        )

    def add_message(self, text: str, sender: str):
        """Ajoute une bulle de message et descend en bas."""
        bubble = ChatBubble(text, sender)
        self._layout.addWidget(bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())


# ─────────────────────────────────────────────
#   BARRE SUPÉRIEURE
# ─────────────────────────────────────────────

class TopBar(QWidget):
    """Barre de titre minimaliste avec indicateur de statut système."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet(
            f"background: {BG_TOPBAR}; border-bottom: 1px solid {BORDER};"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        # Indicateur "SYSTÈME EN LIGNE"
        dot = QLabel("●")
        dot.setFont(QFont(FONT_MAIN, 10))
        dot.setStyleSheet(f"color: {GREEN}; background: transparent;")

        status_text = QLabel("SYSTÈME EN LIGNE")
        status_text.setFont(QFont(FONT_MAIN, 9, QFont.Weight.Bold))
        status_text.setStyleSheet(f"color: {MUTED}; background: transparent; letter-spacing: 1px;")

        # Titre centré
        title = QLabel("A.N.T.O.I.N.E  V1.1")
        title.setFont(QFont(FONT_MAIN, 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {CYAN}; background: transparent; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(dot)
        layout.addSpacing(6)
        layout.addWidget(status_text)
        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        # Espace miroir à gauche pour centrer le titre
        layout.addSpacing(130)


# ─────────────────────────────────────────────
#   BARRE INFÉRIEURE
# ─────────────────────────────────────────────

class BottomBar(QWidget):
    """Barre d'état avec label de statut, bouton stop et bouton microphone."""

    mic_clicked  = pyqtSignal()
    stop_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet(
            f"background: {BG_TOPBAR}; border-top: 1px solid {BORDER};"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        # Label de statut
        self._dot_label   = QLabel("●")
        self._dot_label.setFont(QFont(FONT_CODE, 10))

        self._status_label = QLabel("En veille")
        self._status_label.setFont(QFont(FONT_MAIN, 10))

        layout.addWidget(self._dot_label)
        layout.addSpacing(6)
        layout.addWidget(self._status_label)
        layout.addStretch()

        # Bouton STOP
        self._stop_btn = QPushButton("■")
        self._stop_btn.setFixedSize(QSize(48, 48))
        self._stop_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._stop_btn.setFont(QFont(FONT_MAIN, 16, QFont.Weight.Bold))
        self._stop_btn.setStyleSheet(
            "QPushButton {"
            "  background: #1a0f0f; border-radius: 24px;"
            "  border: 2px solid #ef4444; color: #ef4444;"
            "}"
            "QPushButton:hover {"
            "  background: #ef4444; color: #ffffff;"
            "}"
        )
        self._stop_btn.clicked.connect(self.stop_clicked.emit)
        layout.addSpacing(8)
        layout.addWidget(self._stop_btn)
        layout.addSpacing(8)

        # Bouton microphone
        self._mic_btn = QPushButton("🎤")
        self._mic_btn.setFixedSize(QSize(48, 48))
        self._mic_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._mic_btn.setFont(QFont(FONT_MAIN, 18))
        self._mic_btn.setStyleSheet(self._mic_style_default())
        self._mic_btn.clicked.connect(self.mic_clicked.emit)

        layout.addWidget(self._mic_btn)

        # Timer de clignotement pour l'état "En écoute"
        self._blink_timer  = QTimer(self)
        self._blink_timer.setInterval(600)
        self._blink_timer.timeout.connect(self._blink_dot)
        self._dot_visible  = True

        self._set_status_ui("En veille")

    # ── Styles du bouton ──

    @staticmethod
    def _mic_style_default() -> str:
        return (
            f"QPushButton {{"
            f"  background: {BG_MIC}; border-radius: 24px;"
            f"  border: 2px solid {CYAN}; color: {TEXT};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: {CYAN}; color: #000000;"
            f"}}"
        )

    # ── Mise à jour du statut ──

    def update_status(self, status: str):
        self._set_status_ui(status)

    def _set_status_ui(self, status: str):
        self._blink_timer.stop()
        self._dot_visible = True

        color_map = {
            "En veille":       MUTED,
            "En écoute...":    CYAN,
            "Je réfléchis...": BLUE,
            "Je parle...":     GREEN,
            "Initialisation...": MUTED,
            "Erreur":          "#ef4444",
        }
        color = color_map.get(status, MUTED)

        self._status_label.setText(status)
        self._status_label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )
        self._dot_label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )

        if status == "En écoute...":
            self._blink_timer.start()

    def _blink_dot(self):
        self._dot_visible = not self._dot_visible
        color = CYAN if self._dot_visible else "transparent"
        self._dot_label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )


# ─────────────────────────────────────────────
#   FENÊTRE PRINCIPALE
# ─────────────────────────────────────────────

class MainWindow(QMainWindow):
    """Fenêtre principale de l'interface A.N.T.O.I.N.E."""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._build_ui()
        self._start_thread()

    # ── Configuration de la fenêtre ──

    def _setup_window(self):
        self.setWindowTitle("A.N.T.O.I.N.E — Assistant Vocal IA")
        self.resize(800, 600)
        self.setMinimumSize(600, 400)
        self.setStyleSheet(f"QMainWindow {{ background: {BG_MAIN}; }}")

    # ── Construction de l'interface ──

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background: {BG_MAIN};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Barre supérieure
        self._top_bar = TopBar()
        root.addWidget(self._top_bar)

        # Zone de chat (prend tout l'espace disponible)
        self._chat_area = ChatArea()
        root.addWidget(self._chat_area, stretch=1)

        # Barre inférieure
        self._bottom_bar = BottomBar()
        self._bottom_bar.mic_clicked.connect(self._on_mic_clicked)
        self._bottom_bar.stop_clicked.connect(self._on_stop_clicked)
        root.addWidget(self._bottom_bar)

        # Message de bienvenue
        self._chat_area.add_message(
            "Bonjour ! Dites 'Hey Antoine' ou cliquez sur le micro pour commencer.",
            "antoine",
        )

    # ── Thread assistant ──

    def _start_thread(self):
        self._thread = AssistantThread(self)
        self._thread.message_from_user.connect(self._on_user_message)
        self._thread.message_from_antoine.connect(self._on_antoine_message)
        self._thread.status_changed.connect(self._on_status_changed)
        self._thread.start()

    # ── Slots ──

    def _on_user_message(self, text: str):
        self._chat_area.add_message(text, "user")

    def _on_antoine_message(self, text: str):
        self._chat_area.add_message(text, "antoine")

    def _on_status_changed(self, status: str):
        self._bottom_bar.update_status(status)

    def _on_mic_clicked(self):
        self._thread.trigger_listen()

    def _on_stop_clicked(self):
        self._thread.stop_speech()
        self._bottom_bar.update_status("En veille")

    # ── Fermeture propre ──

    def closeEvent(self, event):
        self._thread.stop()
        self._thread.quit()
        self._thread.wait(3000)
        event.accept()


# ─────────────────────────────────────────────
#   POINT D'ENTRÉE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Palette sombre globale pour les widgets natifs
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(BG_MAIN))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base,            QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG_USER))
    palette.setColor(QPalette.ColorRole.ToolTipBase,     QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.ToolTipText,     QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Text,            QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button,          QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(CYAN))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
