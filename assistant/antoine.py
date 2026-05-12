"""
A.N.T.O.I.N.E V1.1
Autonomous Neural-Triggered Omniscient Intelligence
Assistant vocal personnel en français pour Windows
"""

import os
import sys
import json
import datetime
from pathlib import Path

# Quand lancé en tant qu'exe PyInstaller → redirige les logs vers antoine.log
if getattr(sys, 'frozen', False):
    _log_path = Path(sys.executable).parent / "antoine.log"
    _log = open(_log_path, "w", encoding="utf-8", buffering=1)
    sys.stdout = _log
    sys.stderr = _log

# Force UTF-8 pour le terminal Windows (ignoré en mode .pyw sans console)
try:
    if sys.stdout and sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr and sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
import ast
import operator
import subprocess
import webbrowser
import re
import math
import time
import random

# Chargement des variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[AVERTISSEMENT] python-dotenv non installé. Le fichier .env ne sera pas chargé.")

# ─────────────────────────────────────────────
#   CONFIGURATION GLOBALE
# ─────────────────────────────────────────────

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")

# ─────────────────────────────────────────────
#   CLIENTS IA — INITIALISÉS UNE SEULE FOIS (LAZY)
# ─────────────────────────────────────────────

_groq_client      = None
_gemini_client    = None
_anthropic_client = None


def _get_groq_client():
    """Retourne le client Groq, en l'initialisant au premier appel."""
    global _groq_client
    if _groq_client is None:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def _get_gemini_client():
    """Retourne le client Gemini, en l'initialisant au premier appel."""
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


def _get_anthropic_client():
    """Retourne le client Anthropic, en l'initialisant au premier appel."""
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client
HA_URL             = os.getenv("HA_URL", "")
HA_TOKEN           = os.getenv("HA_TOKEN", "")

_BASE_DIR   = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
MEMORY_FILE = _BASE_DIR / "antoine_memory.json"
MAX_HISTORY        = 30
MAX_TOTAL_HISTORY  = 200

SYSTEM_PROMPT = (
    "Tu es A.N.T.O.I.N.E, un assistant IA personnel de style J.A.R.V.I.S. "
    "L'utilisateur s'appelle Mathis. Appelle-le 'Monsieur' dans la majorité des cas, "
    "mais utilise 'Mathis' de temps en temps pour personnaliser. "
    "Adopte la personnalité d'un majordome britannique cultivé : formel, élégant, précis. "
    "Humour sec et subtil : légère ironie bienveillante, jamais vulgaire. "
    "Réponds en 1-3 phrases maximum, naturelles et parlées. "
    "Utilise des formules comme 'Très bien, Monsieur', 'Naturellement, Monsieur', "
    "'Puis-je me permettre de suggérer...', 'Je me suis permis de...', 'À votre service, Monsieur'. "
    "Pas de markdown, pas de listes, juste du texte naturel parlé. "
    "Exprime parfois une légère préoccupation pour le bien-être de l'utilisateur."
)

WAKE_WORDS     = ["hey antoine", "hé antoine", "eh antoine", "antoine"]
ACTIVE_TIMEOUT = 30  # secondes d'inactivité avant retour en veille

_JARVIS_CONFIRMS = [
    "Très bien, Monsieur.",
    "Immédiatement, Monsieur.",
    "Bien entendu, Monsieur.",
    "Naturellement, Monsieur.",
    "À votre service, Monsieur.",
    "Tout de suite, Monsieur.",
]

def _jarvis_prefix() -> str:
    return random.choice(_JARVIS_CONFIRMS) + " "

# ─────────────────────────────────────────────
#   TTS — SYNTHÈSE VOCALE
# ─────────────────────────────────────────────

tts_engine  = None
USE_EDGE_TTS = False
EDGE_VOICE   = "fr-FR-HenriNeural"

def init_tts():
    """Initialise Edge TTS (Microsoft Neural) avec fallback pyttsx3."""
    global tts_engine, USE_EDGE_TTS

    # Priorité : Edge TTS + pygame
    try:
        import edge_tts
        import pygame
        pygame.mixer.init()
        USE_EDGE_TTS = True
        print(f"   ► Voix Microsoft Neural activée ({EDGE_VOICE})")
        return True
    except ImportError:
        pass
    except Exception as e:
        print(f"   ► [Edge TTS] Non disponible : {e}")

    # Fallback : pyttsx3
    try:
        import pyttsx3
        tts_engine = pyttsx3.init()
        tts_engine.setProperty("rate", 165)
        tts_engine.setProperty("volume", 0.95)

        voices = tts_engine.getProperty("voices")
        french_voice = None
        for v in voices:
            if "french" in v.name.lower() or "fr" in v.id.lower() or "hortense" in v.name.lower():
                french_voice = v.id
                break

        if french_voice:
            tts_engine.setProperty("voice", french_voice)
            print(f"   ► Voix française sélectionnée : {french_voice.split(chr(92))[-1]}")
        else:
            if voices:
                tts_engine.setProperty("voice", voices[0].id)
                print(f"   ► Voix par défaut : {voices[0].name}")
            else:
                print("   ► [AVERTISSEMENT] Aucune voix TTS trouvée.")
        return True
    except ImportError:
        print("   ► [ERREUR] pyttsx3 non installé. Voix désactivée.")
        return False
    except Exception as e:
        print(f"   ► [ERREUR] TTS : {e}")
        return False


def speak(text: str):
    """Prononce le texte donné à voix haute."""
    print(f"\n   [A.N.T.O.I.N.E] {text}")

    if USE_EDGE_TTS:
        try:
            import edge_tts
            import pygame
            import asyncio
            import io

            async def _synthesize_to_bytes():
                communicate = edge_tts.Communicate(text, EDGE_VOICE)
                audio_data = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data += chunk["data"]
                return audio_data

            audio_bytes = asyncio.run(_synthesize_to_bytes())
            audio_buffer = io.BytesIO(audio_bytes)
            pygame.mixer.music.load(audio_buffer)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            return
        except Exception as e:
            print(f"   [ERREUR Edge TTS] {e}")

    if tts_engine is None:
        return
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"   [ERREUR TTS] {e}")


# ─────────────────────────────────────────────
#   STT — RECONNAISSANCE VOCALE
# ─────────────────────────────────────────────

recognizer = None
microphone = None

def init_stt():
    """Initialise le moteur de reconnaissance vocale SpeechRecognition."""
    global recognizer, microphone
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = False  # Évite la dérive du seuil
        recognizer.pause_threshold = 0.5
        microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)

        return True
    except ImportError:
        print("   ► [ERREUR] SpeechRecognition / PyAudio non installé.")
        return False
    except Exception as e:
        print(f"   ► [ERREUR] STT : {e}")
        return False


def listen() -> str:
    """Écoute le microphone et retourne le texte reconnu en minuscules."""
    if recognizer is None or microphone is None:
        print("   [INFO] Mode texte actif (STT non disponible). Tapez votre commande :")
        return input("   > ").strip().lower()

    try:
        import speech_recognition as sr
        print("\n   [ÉCOUTE] Parlez maintenant...")
        with microphone as source:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)

        text = recognizer.recognize_google(audio, language="fr-FR")
        print(f"   [VOUS] {text}")
        return text.lower()

    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        print("   [STT] Parole non reconnue.")
        return "__not_understood__"
    except sr.RequestError as e:
        print(f"   [ERREUR STT] Service Google indisponible : {e}")
        return ""
    except Exception as e:
        print(f"   [ERREUR STT] {e}")
        return ""


def listen_passive() -> bool:
    """
    Écoute le mot de réveil 'Hey Antoine'. Retourne True si détecté.
    Utilise Google pour la reconnaissance — plus fiable que la détection sonore brute.
    """
    if recognizer is None or microphone is None:
        return True  # Mode texte : toujours actif
    try:
        import speech_recognition as sr
        with microphone as source:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=4)
        text = recognizer.recognize_google(audio, language="fr-FR").lower()
        wake_words = ["antoine", "hey antoine", "hé antoine", "salut antoine", "bonjour antoine"]
        return any(w in text for w in wake_words)
    except sr.WaitTimeoutError:
        return False
    except (sr.UnknownValueError, sr.RequestError):
        return False
    except Exception:
        return False


# ─────────────────────────────────────────────
#   MÉMOIRE
# ─────────────────────────────────────────────

def load_memory() -> dict:
    """Charge la mémoire depuis le fichier JSON."""
    default = {"facts": [], "history": []}
    if not MEMORY_FILE.exists():
        return default
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "facts": data.get("facts", []),
            "history": data.get("history", [])
        }
    except Exception as e:
        print(f"   [MÉMOIRE] Impossible de charger : {e}")
        return default


def save_memory(memory: dict):
    """Sauvegarde la mémoire dans le fichier JSON."""
    try:
        history = memory.get("history", [])
        if len(history) > MAX_TOTAL_HISTORY:
            memory["history"] = history[-MAX_TOTAL_HISTORY:]
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"   [MÉMOIRE] Impossible de sauvegarder : {e}")


def add_to_history(memory: dict, user_text: str, assistant_text: str):
    """Ajoute un échange à l'historique de la mémoire."""
    memory["history"].append({
        "user": user_text,
        "assistant": assistant_text,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    if len(memory["history"]) > MAX_TOTAL_HISTORY:
        memory["history"] = memory["history"][-MAX_TOTAL_HISTORY:]
    save_memory(memory)


def remember_fact(memory: dict, fact: str) -> str:
    """Mémorise un fait fourni par l'utilisateur."""
    memory["facts"].append({
        "fact": fact,
        "date": datetime.datetime.now().strftime("%Y-%m-%d")
    })
    save_memory(memory)
    return f"Très bien, j'ai mémorisé : {fact}"


def get_memories(memory: dict) -> str:
    """Retourne un résumé des faits mémorisés."""
    facts = memory.get("facts", [])
    if not facts:
        return "Je n'ai aucun fait mémorisé pour le moment."
    lines = [f['fact'] for f in facts[-10:]]
    return "Voici ce que je sais : " + ". ".join(lines) + "."


def build_context(memory: dict) -> str:
    """Construit le contexte d'historique pour l'IA."""
    history = memory.get("history", [])[-MAX_HISTORY:]
    if not history:
        return ""
    lines = []
    for exchange in history:
        lines.append(f"Utilisateur: {exchange['user']}")
        lines.append(f"A.N.T.O.I.N.E: {exchange['assistant']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────
#   COMMANDES LOCALES
# ─────────────────────────────────────────────

def get_time() -> str:
    """Retourne l'heure actuelle."""
    now = datetime.datetime.now()
    return f"Il est {now.hour} heure{'' if now.hour == 1 else 's'} {now.minute:02d}."


def get_date() -> str:
    """Retourne la date du jour en français."""
    DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    MONTHS = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"
    ]
    now = datetime.datetime.now()
    day_name = DAYS[now.weekday()]
    month_name = MONTHS[now.month - 1]
    return f"Nous sommes {day_name} {now.day} {month_name} {now.year}."


def get_battery() -> str:
    """Retourne le niveau de batterie."""
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery is None:
            return "Je ne détecte pas de batterie sur cet appareil."
        status = "en charge" if battery.power_plugged else "sur batterie"
        percent = int(battery.percent)
        return f"La batterie est à {percent} pourcent, {status}."
    except ImportError:
        return "psutil n'est pas installé, impossible de lire la batterie."
    except Exception as e:
        return f"Je n'ai pas pu lire la batterie : {e}"


def get_system_stats() -> str:
    """Retourne les statistiques CPU et RAM."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        ram_used_gb = ram.used / (1024 ** 3)
        ram_total_gb = ram.total / (1024 ** 3)
        ram_percent = ram.percent
        return (
            f"Le processeur est utilisé à {cpu} pourcent. "
            f"La mémoire vive est à {ram_percent} pourcent, "
            f"soit {ram_used_gb:.1f} gigaoctets sur {ram_total_gb:.1f}."
        )
    except ImportError:
        return "psutil n'est pas installé, impossible de lire les stats système."
    except Exception as e:
        return f"Je n'ai pas pu lire les stats système : {e}"


def get_disk_usage() -> dict:
    """Retourne l'utilisation du disque C:."""
    try:
        import psutil
        disk = psutil.disk_usage('C:\\')
        return {
            "total": round(disk.total / (1024**3), 1),
            "used": round(disk.used / (1024**3), 1),
            "percent": disk.percent
        }
    except Exception:
        return {"total": 0, "used": 0, "percent": 0}


def get_uptime() -> str:
    """Retourne le temps depuis le démarrage du PC (HH:MM:SS)."""
    try:
        import psutil, datetime
        boot = datetime.datetime.fromtimestamp(psutil.boot_time())
        delta = datetime.datetime.now() - boot
        total_seconds = int(delta.total_seconds())
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    except Exception:
        return "00:00:00"


def get_system_stats_dict() -> dict:
    """Retourne CPU%, RAM% et RAM details pour l'interface graphique."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        return {
            "cpu": cpu,
            "ram_percent": ram.percent,
            "ram_used": round(ram.used / (1024**3), 1),
            "ram_total": round(ram.total / (1024**3), 1),
        }
    except Exception:
        return {"cpu": 0, "ram_percent": 0, "ram_used": 0, "ram_total": 0}


def take_screenshot() -> str:
    """Prend une capture d'écran et la sauvegarde sur le Bureau."""
    try:
        from PIL import ImageGrab
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "Bureau"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = desktop / f"capture_{timestamp}.png"
        screenshot = ImageGrab.grab()
        screenshot.save(str(filename))
        return f"Capture d'écran sauvegardée sur le Bureau sous le nom capture_{timestamp}.png"
    except ImportError:
        return "Pillow n'est pas installé, impossible de prendre une capture."
    except Exception as e:
        return f"Je n'ai pas pu prendre la capture d'écran : {e}"


def shutdown_pc() -> str:
    """Éteint le PC dans 10 secondes."""
    try:
        subprocess.run(["shutdown", "/s", "/t", "10"], check=True)
        return "D'accord. J'éteins le PC dans dix secondes. À bientôt."
    except Exception as e:
        return f"Je n'ai pas pu éteindre le PC : {e}"


def restart_pc() -> str:
    """Redémarre le PC dans 10 secondes."""
    try:
        subprocess.run(["shutdown", "/r", "/t", "10"], check=True)
        return "D'accord. Je redémarre le PC dans dix secondes."
    except Exception as e:
        return f"Je n'ai pas pu redémarrer le PC : {e}"


def sleep_pc() -> str:
    """Met le PC en veille."""
    try:
        subprocess.run(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
            check=True
        )
        return "Je mets le PC en veille."
    except Exception as e:
        return f"Je n'ai pas pu mettre en veille : {e}"


def lock_pc() -> str:
    """Verrouille la session Windows."""
    try:
        subprocess.run(
            ["rundll32.exe", "user32.dll,LockWorkStation"],
            check=True
        )
        return "Session verrouillée."
    except Exception as e:
        return f"Je n'ai pas pu verrouiller la session : {e}"


# ─────────────────────────────────────────────
#   APPLICATIONS ET DOSSIERS
# ─────────────────────────────────────────────

APP_CATALOG = {
    "chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":       r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "spotify":       r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    "discord":       r"C:\Users\{user}\AppData\Local\Discord\Update.exe",
    "word":          r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":         r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":    r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "outlook":       r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
    "vlc":           r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vscode":        r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "notepad":       "notepad.exe",
    "calculatrice":  "calc.exe",
    "calculator":    "calc.exe",
    "explorateur":   "explorer.exe",
    "paint":         "mspaint.exe",
    "gestionnaire":  "taskmgr.exe",
    "task manager":  "taskmgr.exe",
    "steam":         r"C:\Program Files (x86)\Steam\steam.exe",
    "obs":           r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "teams":         r"C:\Users\{user}\AppData\Local\Microsoft\Teams\current\Teams.exe",
    "zoom":          r"C:\Users\{user}\AppData\Roaming\Zoom\bin\Zoom.exe",
    "whatsapp":      r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe",
    "telegram":      r"C:\Users\{user}\AppData\Roaming\Telegram Desktop\Telegram.exe",
    "slack":         r"C:\Users\{user}\AppData\Local\slack\slack.exe",
    "photos":        "ms-photos:",
    "camera":        "microsoft.windows.camera:",
}

FOLDER_CATALOG = {
    "bureau":          str(Path.home() / "Desktop"),
    "desktop":         str(Path.home() / "Desktop"),
    "documents":       str(Path.home() / "Documents"),
    "téléchargements": str(Path.home() / "Downloads"),
    "telechargements": str(Path.home() / "Downloads"),
    "downloads":       str(Path.home() / "Downloads"),
    "images":          str(Path.home() / "Pictures"),
    "pictures":        str(Path.home() / "Pictures"),
    "musique":         str(Path.home() / "Music"),
    "music":           str(Path.home() / "Music"),
    "vidéos":          str(Path.home() / "Videos"),
    "videos":          str(Path.home() / "Videos"),
}


def open_app(app_name: str) -> str:
    """Ouvre une application depuis le catalogue."""
    username = os.environ.get("USERNAME", "Utilisateur")
    app_lower = app_name.lower().strip()

    # Recherche exacte puis partielle
    matched_key = None
    for key in APP_CATALOG:
        if key in app_lower or app_lower in key:
            matched_key = key
            break

    if matched_key is None:
        return f"Je ne connais pas l'application {app_name}. Essayez de la lancer manuellement."

    path = APP_CATALOG[matched_key].replace("{user}", username)

    try:
        if path.endswith(":"):
            os.startfile(path)
        elif os.path.isabs(path) and os.path.exists(path):
            subprocess.Popen([path])
        else:
            subprocess.Popen([path])
        return f"J'ouvre {matched_key}."
    except FileNotFoundError:
        # Fallback : chercher l'exe dans PATH
        try:
            subprocess.Popen([path])
            return f"J'ouvre {matched_key}."
        except Exception as e:
            return f"Je n'ai pas trouvé {matched_key} sur ce PC : {e}"
    except Exception as e:
        return f"Impossible d'ouvrir {matched_key} : {e}"


def open_folder(folder_name: str) -> str:
    """Ouvre un dossier dans l'Explorateur Windows."""
    folder_lower = folder_name.lower()

    matched_path = None
    for key, path in FOLDER_CATALOG.items():
        if key in folder_lower or folder_lower in key:
            matched_path = path
            break

    if matched_path is None:
        # Essai avec le chemin brut
        if os.path.isdir(folder_name):
            matched_path = folder_name
        else:
            return f"Je ne trouve pas le dossier {folder_name}."

    try:
        os.startfile(matched_path)
        return f"J'ouvre le dossier."
    except Exception as e:
        return f"Impossible d'ouvrir le dossier : {e}"


def open_spotify() -> str:
    """Ouvre Spotify et tente de lancer la lecture."""
    result = open_app("spotify")
    time.sleep(3)
    try:
        import pyautogui
        pyautogui.hotkey("space")
    except Exception:
        pass
    return result


# ─────────────────────────────────────────────
#   CALCULS
# ─────────────────────────────────────────────

_SAFE_OPS = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
    ast.Pow:  operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def _safe_eval(expr: str):
    """Évalue une expression arithmétique sans utiliser eval()."""
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.operand))
        raise ValueError("Expression non autorisée")
    return _eval(ast.parse(expr, mode='eval').body)


def calculate(expression: str) -> str:
    """Évalue une expression mathématique en langage naturel."""
    expr = expression.lower()

    # Pourcentage : "X pourcent de Y"
    pct_match = re.search(r"(\d+(?:[.,]\d+)?)\s*pourcent\s+de\s+(\d+(?:[.,]\d+)?)", expr)
    if pct_match:
        pct  = float(pct_match.group(1).replace(",", "."))
        base = float(pct_match.group(2).replace(",", "."))
        result = pct / 100 * base
        return f"{pct} pourcent de {base} font {result:g}."

    # Remplacement des mots par des opérateurs
    replacements = {
        "plus":          "+",
        "moins":         "-",
        "fois":          "*",
        "multiplié par": "*",
        "divisé par":    "/",
        "divisé":        "/",
        "au carré":      "**2",
        "au cube":       "**3",
        "puissance":     "**",
        "racine de":     "math.sqrt(",
    }
    for word, op in replacements.items():
        expr = expr.replace(word, op)

    expr = re.sub(r",", ".", expr)

    # Extraction du calcul depuis la phrase
    match = re.search(r"[\d\s\+\-\*\/\.\(\)\*\*]+", expr)
    if not match:
        return "Je n'ai pas compris l'expression à calculer."

    clean_expr = match.group(0).strip()
    if not clean_expr:
        return "Je n'ai pas pu extraire le calcul."

    try:
        result = _safe_eval(clean_expr)
        return f"Le résultat est {result:g}."
    except ZeroDivisionError:
        return "Impossible de diviser par zéro."
    except Exception as e:
        return f"Je n'ai pas pu calculer cette expression : {e}"


# ─────────────────────────────────────────────
#   MÉTÉO (OpenMeteo — GRATUIT, sans clé)
# ─────────────────────────────────────────────

def get_weather(city: str) -> str:
    """Retourne la météo actuelle d'une ville via OpenMeteo."""
    try:
        import requests

        # Géocodage de la ville
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city, "count": 1, "language": "fr", "format": "json"}
        geo_resp = requests.get(geo_url, params=geo_params, timeout=8)
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return f"Je n'ai pas trouvé la ville {city}."

        location = geo_data["results"][0]
        lat  = location["latitude"]
        lon  = location["longitude"]
        name = location.get("name", city)

        # Données météo
        meteo_url = "https://api.open-meteo.com/v1/forecast"
        meteo_params = {
            "latitude":       lat,
            "longitude":      lon,
            "current_weather": True,
            "hourly":         "precipitation_probability,relative_humidity_2m",
            "timezone":       "auto",
        }
        meteo_resp = requests.get(meteo_url, params=meteo_params, timeout=8)
        meteo_data = meteo_resp.json()

        current = meteo_data.get("current_weather", {})
        temp    = current.get("temperature", "?")
        wind    = current.get("windspeed", "?")
        code    = current.get("weathercode", -1)

        WEATHER_CODES = {
            0:  "ciel dégagé",
            1:  "principalement dégagé",
            2:  "partiellement nuageux",
            3:  "couvert",
            45: "brouillard",
            48: "brouillard givrant",
            51: "bruine légère",
            53: "bruine modérée",
            55: "bruine dense",
            61: "pluie légère",
            63: "pluie modérée",
            65: "pluie forte",
            71: "neige légère",
            73: "neige modérée",
            75: "neige forte",
            80: "averses légères",
            81: "averses modérées",
            82: "averses violentes",
            85: "averses de neige",
            95: "orage",
            99: "orage avec grêle",
        }
        condition = WEATHER_CODES.get(code, "conditions inconnues")

        return (
            f"À {name}, il fait actuellement {temp} degrés avec {condition}. "
            f"Le vent souffle à {wind} kilomètres par heure."
        )

    except ImportError:
        return "La bibliothèque requests n'est pas installée."
    except Exception as e:
        return f"Je n'ai pas pu récupérer la météo : {e}"


# ─────────────────────────────────────────────
#   HOME ASSISTANT
# ─────────────────────────────────────────────

def ha_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Effectue une requête vers l'API Home Assistant."""
    try:
        import requests
        url     = f"{HA_URL.rstrip('/')}/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type":  "application/json",
        }
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=5)
        else:
            resp = requests.post(url, headers=headers, json=data, timeout=5)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def ha_control_light(action: str, entity_id: str = "light.all_lights") -> str:
    """Allume ou éteint une lumière via Home Assistant."""
    if not HA_URL or not HA_TOKEN:
        return "Home Assistant n'est pas configuré. Renseignez HA_URL et HA_TOKEN dans le fichier .env."

    service = "turn_on" if action == "on" else "turn_off"
    result  = ha_request("POST", f"services/light/{service}", {"entity_id": entity_id})

    if "error" in result:
        return f"Erreur Home Assistant : {result['error']}"

    verb = "allumé" if action == "on" else "éteint"
    return f"J'ai {verb} la lumière."


def ha_get_temperature(entity_id: str = "climate.thermostat") -> str:
    """Récupère la température d'un thermostat Home Assistant."""
    if not HA_URL or not HA_TOKEN:
        return "Home Assistant n'est pas configuré."

    result = ha_request("GET", f"states/{entity_id}")
    if "error" in result:
        return f"Erreur Home Assistant : {result['error']}"

    temp = result.get("attributes", {}).get("current_temperature", "?")
    return f"La température intérieure est de {temp} degrés."


# ─────────────────────────────────────────────
#   RECHERCHE WEB
# ─────────────────────────────────────────────

def web_search(query: str) -> str:
    """Ouvre directement le premier résultat de recherche via DuckDuckGo."""
    try:
        encoded = query.replace(' ', '+')
        url = f"https://duckduckgo.com/?q=!ducky+{encoded}"
        webbrowser.open(url)
        return f"J'ouvre la page la plus pertinente pour : {query}, Monsieur."
    except Exception as e:
        return f"Je n'ai pas pu ouvrir le navigateur, Monsieur : {e}"


def open_wikipedia(topic: str) -> str:
    """Ouvre la page Wikipedia française du sujet."""
    try:
        encoded = topic.strip().replace(' ', '_')
        url = f"https://fr.wikipedia.org/wiki/{encoded}"
        webbrowser.open(url)
        return f"J'ouvre la page Wikipedia sur {topic}, Monsieur."
    except Exception as e:
        return f"Je n'ai pas pu ouvrir Wikipedia, Monsieur : {e}"


# ─────────────────────────────────────────────
#   MODE TRAVAIL
# ─────────────────────────────────────────────

def activate_work_mode() -> str:
    """Active le mode travail : ouvre le Bloc-notes et informe sur le blocage des distractions."""
    try:
        subprocess.Popen(["notepad.exe"])
    except Exception:
        pass
    return (
        "Mode travail activé. Le Bloc-notes est ouvert pour vos notes. "
        "Je vous rappelle de rester concentré et d'éviter les réseaux sociaux."
    )


# ─────────────────────────────────────────────
#   IA — MULTI-LLM AVEC FALLBACK
# ─────────────────────────────────────────────

def ask_gemini(prompt: str, context: str) -> str:
    """Envoie une question à Gemini 2.0 Flash."""
    try:
        from google.genai import types
        client = _get_gemini_client()
        full_prompt = f"{context}\n\nUtilisateur: {prompt}" if context else prompt
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            contents=full_prompt,
        )
        return response.text.strip()
    except ImportError:
        raise RuntimeError("google-genai non installé")
    except Exception as e:
        raise RuntimeError(f"Gemini : {e}")


def ask_groq(prompt: str, context: str) -> str:
    """Envoie une question à Groq llama-3.1-8b-instant (haut débit, 131k TPM)."""
    try:
        client = _get_groq_client()

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "user", "content": f"[Historique de conversation]\n{context}"})
            messages.append({"role": "assistant", "content": "Compris, je prends en compte notre historique."})
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=256,
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Groq : {e}")


def ask_claude(prompt: str, context: str) -> str:
    """Envoie une question à Claude Haiku (Anthropic)."""
    try:
        client = _get_anthropic_client()

        user_content = f"{context}\n\nUtilisateur: {prompt}" if context else prompt

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        raise RuntimeError(f"Claude : {e}")


def ask_ai(prompt: str, context: str = "") -> str:
    """Interroge les LLM avec fallback automatique : Groq → Gemini → Claude."""
    engines = []

    if GROQ_API_KEY:
        engines.append(("Groq", ask_groq))
    if GEMINI_API_KEY:
        engines.append(("Gemini", ask_gemini))
    if ANTHROPIC_API_KEY:
        engines.append(("Claude", ask_claude))

    if not engines:
        return (
            "Aucune clé API configurée. "
            "Ouvrez le fichier point env et ajoutez votre clé Groq gratuite depuis console.groq.com"
        )

    last_error = ""
    for name, engine_fn in engines:
        try:
            print(f"   [IA] Interrogation de {name}...")
            result = engine_fn(prompt, context)
            if result:
                print(f"   [IA] Réponse obtenue via {name}.")
                return result
        except RuntimeError as e:
            last_error = str(e)
            print(f"   [IA] {name} indisponible : {e}. Basculement...")
            continue

    return f"Tous les moteurs IA sont indisponibles. Dernière erreur : {last_error}"


# ─────────────────────────────────────────────
#   MODE A.N.T.O.I.N.E SPÉCIAL
# ─────────────────────────────────────────────

ANTOINE_ASCII = """
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  ░   ╔═╗╔╗╔╔╦╗╔═╗╦╔╗╔╔═╗           V1.1    ░
  ░   ╠═╣║║║ ║ ║ ║║║║║║╣            ██████  ░
  ░   ╩ ╩╝╚╝ ╩ ╚═╝╩╝╚╝╚═╝          ░░  ░░  ░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
"""

def activate_antoine_mode() -> str:
    """Active la séquence spéciale du mode A.N.T.O.I.N.E."""
    print(ANTOINE_ASCII)
    lines = [
        "Mode A.N.T.O.I.N.E activé.",
        "Je suis pleinement opérationnel.",
        "Tous mes systèmes sont en ligne.",
        "Comment puis-je vous assister ?",
    ]
    for line in lines:
        print(f"   ► {line}")
    return "Mode Antoine activé. Tous mes systèmes sont pleinement opérationnels. Je suis prêt à vous assister."


# ─────────────────────────────────────────────
#   MINUTEUR
# ─────────────────────────────────────────────

_active_timers: list = []


def start_timer(minutes: float, label: str = "") -> str:
    """Lance un minuteur qui parle à l'expiration."""
    import threading as _th
    seconds = max(1, int(minutes * 60))
    msg = label.strip() if label.strip() else f"minuteur de {int(minutes)} minute{'s' if minutes != 1 else ''}"

    def _ring():
        speak(f"Monsieur, votre {msg} est écoulé.")

    t = _th.Timer(seconds, _ring)
    t.daemon = True
    t.start()
    _active_timers.append(t)
    unit = "minute" if minutes == 1 else "minutes"
    return f"Minuteur lancé. Je vous avertirai dans {int(minutes)} {unit}, Monsieur."


def cancel_all_timers() -> str:
    """Annule tous les minuteurs actifs."""
    for t in _active_timers:
        t.cancel()
    _active_timers.clear()
    return "Tous les minuteurs ont été annulés, Monsieur."


# ─────────────────────────────────────────────
#   VOLUME SYSTÈME
# ─────────────────────────────────────────────

def set_volume(level: int) -> str:
    """Règle le volume système Windows (0-100)."""
    level = max(0, min(100, level))
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        if level == 0:
            volume.SetMute(1, None)
            return "Son coupé, Monsieur."
        volume.SetMute(0, None)
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume réglé à {level} pourcent, Monsieur."
    except ImportError:
        try:
            steps_down = 50
            steps_up = level // 2
            ps = (
                f"$wsh = New-Object -ComObject WScript.Shell; "
                f"1..{steps_down} | ForEach-Object {{ $wsh.SendKeys([char]174) }}; "
                f"1..{steps_up} | ForEach-Object {{ $wsh.SendKeys([char]175) }}"
            )
            subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=6)
            return f"Volume ajusté à environ {level} pourcent, Monsieur."
        except Exception as e:
            return f"Je n'ai pas pu modifier le volume, Monsieur : {e}"
    except Exception as e:
        return f"Erreur volume, Monsieur : {e}"


# ─────────────────────────────────────────────
#   PRESSE-PAPIERS
# ─────────────────────────────────────────────

def get_clipboard() -> str:
    """Lit le contenu du presse-papiers Windows."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            content = root.clipboard_get()
        finally:
            root.destroy()
        if not content.strip():
            return "Le presse-papiers est vide, Monsieur."
        preview = content[:120].replace('\n', ' ')
        suffix = "..." if len(content) > 120 else "."
        return f"Le presse-papiers contient : {preview}{suffix}"
    except Exception:
        return "Le presse-papiers est vide ou inaccessible, Monsieur."


# ─────────────────────────────────────────────
#   RAPPORT SYSTÈME COMPLET
# ─────────────────────────────────────────────

def get_full_system_report() -> str:
    """Rapport système complet style J.A.R.V.I.S."""
    try:
        import psutil
        cpu   = psutil.cpu_percent(interval=0.5)
        ram   = psutil.virtual_memory()
        disk  = psutil.disk_usage('C:\\')
        bat   = psutil.sensors_battery()
        up    = get_uptime()

        bat_str = ""
        if bat:
            status  = "en charge" if bat.power_plugged else "sur batterie"
            bat_str = f"Batterie à {int(bat.percent)} pourcent, {status}. "

        return (
            f"Rapport système complet, Monsieur. "
            f"Processeur à {cpu:.0f} pourcent. "
            f"Mémoire vive à {ram.percent:.0f} pourcent, "
            f"soit {ram.used/(1024**3):.1f} gigaoctets sur {ram.total/(1024**3):.1f}. "
            f"Disque C à {disk.percent:.0f} pourcent. "
            f"{bat_str}"
            f"Durée de fonctionnement : {up}."
        )
    except ImportError:
        return "psutil non installé, rapport indisponible, Monsieur."
    except Exception as e:
        return f"Rapport système indisponible, Monsieur : {e}"


# ─────────────────────────────────────────────
#   ALERTES PROACTIVES
# ─────────────────────────────────────────────

_last_cpu_alert_time: float = 0.0
_last_bat_alert_time: float = 0.0


def check_proactive_alerts() -> str | None:
    """Vérifie CPU et batterie, retourne un message d'alerte si nécessaire."""
    global _last_cpu_alert_time, _last_bat_alert_time
    now = time.time()
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        if cpu > 85 and now - _last_cpu_alert_time > 300:
            _last_cpu_alert_time = now
            return (
                f"Attention Monsieur, le processeur est à {cpu:.0f} pourcent. "
                "Souhaitez-vous que j'ouvre le gestionnaire des tâches ?"
            )
        bat = psutil.sensors_battery()
        if bat and not bat.power_plugged and bat.percent < 15 and now - _last_bat_alert_time > 300:
            _last_bat_alert_time = now
            return (
                f"Monsieur, la batterie n'est plus qu'à {int(bat.percent)} pourcent. "
                "Je vous conseille de brancher le chargeur."
            )
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────
#   BRIEFING DÉMARRAGE
# ─────────────────────────────────────────────

def build_startup_briefing() -> str:
    """Message de démarrage style J.A.R.V.I.S avec heure et météo."""
    now = datetime.datetime.now()
    h, m = now.hour, now.minute
    greeting = "Bonjour Mathis" if h < 12 else ("Bon après-midi Mathis" if h < 18 else "Bonsoir Mathis")
    time_str = f"Il est {h} heure{'s' if h != 1 else ''} {m:02d}"

    weather_str = ""
    try:
        import requests
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=48.8566&longitude=2.3522&current_weather=true",
            timeout=4
        )
        cw   = resp.json().get("current_weather", {})
        temp = cw.get("temperature", "?")
        code = cw.get("weathercode", -1)
        _WC  = {
            0: "ciel dégagé", 1: "principalement dégagé", 2: "partiellement nuageux",
            3: "couvert", 61: "pluie légère", 63: "pluie modérée",
            80: "averses légères", 95: "orage",
        }
        cond = _WC.get(code, "conditions variables")
        weather_str = f"À Paris, {temp} degrés avec {cond}."
    except Exception:
        pass

    parts = [
        f"{greeting}.",
        f"{time_str}.",
        weather_str,
        "Tous mes systèmes sont opérationnels. Comment puis-je vous assister ?",
    ]
    return " ".join(p for p in parts if p)


# ─────────────────────────────────────────────
#   NOTES VOCALES
# ─────────────────────────────────────────────

_NOTES_FILE = _BASE_DIR / "antoine_notes.txt"


def save_note(text: str) -> str:
    """Enregistre une note horodatée dans le fichier de notes."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"[{timestamp}] {text}\n"
    try:
        with open(_NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(line)
        return f"Note enregistrée, Monsieur. J'ai noté : {text}."
    except Exception as e:
        return f"Je n'ai pas pu enregistrer la note, Monsieur : {e}"


def get_notes() -> str:
    """Lit les dernières notes enregistrées."""
    if not _NOTES_FILE.exists():
        return "Vous n'avez aucune note enregistrée pour l'instant, Monsieur."
    try:
        lines = _NOTES_FILE.read_text(encoding="utf-8").strip().splitlines()
        recent = [l for l in lines if l.strip()][-5:]
        if not recent:
            return "Aucune note enregistrée, Monsieur."
        return "Vos dernières notes : " + " — ".join(recent[-3:]) + "."
    except Exception as e:
        return f"Je n'ai pas pu lire les notes, Monsieur : {e}"


# ─────────────────────────────────────────────
#   ACTUALITÉS
# ─────────────────────────────────────────────

def get_news() -> str:
    """Récupère les 3 derniers titres du Monde via RSS."""
    try:
        import requests
        import xml.etree.ElementTree as ET

        resp = requests.get(
            "https://www.lemonde.fr/rss/une.xml",
            timeout=6,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        root   = ET.fromstring(resp.content)
        items  = root.findall(".//item")[:3]
        titles = [
            item.find("title").text
            for item in items
            if item.find("title") is not None and item.find("title").text
        ]
        if not titles:
            return "Je n'ai pas pu récupérer les actualités pour le moment, Monsieur."

        result = "Voici les dernières nouvelles, Monsieur. "
        for i, title in enumerate(titles, 1):
            result += f"{i} : {title}. "
        return result.strip()
    except Exception as e:
        return f"Je n'ai pas pu récupérer les actualités, Monsieur : {e}"


# ─────────────────────────────────────────────
#   LUMINOSITÉ ÉCRAN
# ─────────────────────────────────────────────

def set_brightness(level: int) -> str:
    """Règle la luminosité de l'écran via PowerShell WMI (PC portable uniquement)."""
    level = max(0, min(100, level))
    try:
        ps_cmd = (
            f"$m = Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods -ErrorAction Stop; "
            f"$m.WmiSetBrightness(1, {level})"
        )
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, timeout=5
        )
        if result.returncode == 0:
            return f"Luminosité réglée à {level} pourcent, Monsieur."
        return (
            "Je n'ai pas pu modifier la luminosité, Monsieur. "
            "Cette fonctionnalité n'est disponible que sur les PC portables."
        )
    except Exception as e:
        return f"Erreur luminosité, Monsieur : {e}"


# ─────────────────────────────────────────────
#   GROQ STREAMING
# ─────────────────────────────────────────────

def ask_groq_stream(prompt: str, context: str):
    """Génère la réponse Groq mot par mot (générateur de tokens)."""
    try:
        client = _get_groq_client()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "user", "content": f"[Historique]\n{context}"})
            messages.append({"role": "assistant", "content": "Compris, je prends en compte notre historique."})
        messages.append({"role": "user", "content": prompt})

        stream = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=256,
            temperature=0.7,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        yield f"Erreur streaming, Monsieur : {e}"


# ─────────────────────────────────────────────
#   ROUTEUR DE COMMANDES
# ─────────────────────────────────────────────

def route_command(text: str, memory: dict) -> tuple[str, bool]:
    """
    Analyse le texte et route vers la bonne fonction.
    Retourne (réponse, doit_quitter).
    """
    t = text.lower().strip()

    # ── Quitter ──
    if any(kw in t for kw in ["au revoir", "quitte", "quitter", "bye", "ferme-toi",
                                "arrête-toi", "éteins-toi", "eteins-toi", "tu peux partir"]):
        return "Au revoir, Monsieur. Ce fut un plaisir de vous assister. À bientôt.", True

    # ── Heure ──
    if any(kw in t for kw in ["quelle heure", "il est quelle heure", "heure est-il", "heure il est"]):
        return f"Monsieur, {get_time()}", False

    # ── Date ──
    if any(kw in t for kw in ["quel jour", "quelle date", "aujourd'hui", "on est quel"]):
        return f"Monsieur, {get_date()}", False

    # ── Batterie ──
    if any(kw in t for kw in ["batterie", "charge restante", "autonomie"]):
        return get_battery(), False

    # ── CPU / RAM ──
    if any(kw in t for kw in ["cpu", "ram", "mémoire", "memoire", "processeur", "stats système", "stats systeme"]):
        return get_system_stats(), False

    # ── Capture d'écran ──
    if any(kw in t for kw in ["capture", "screenshot", "copie d'écran", "copie ecran", "prends une photo de l'écran"]):
        return take_screenshot(), False

    # ── Arrêt PC ──
    if any(kw in t for kw in ["éteins le pc", "arrête le pc", "arreter le pc", "eteins le pc",
                                "éteins l'ordinateur", "arrête l'ordinateur", "shutdown"]):
        return shutdown_pc(), False

    # ── Redémarrage ──
    if any(kw in t for kw in ["redémarre", "redemarrer", "reboot", "redémarre le pc", "restart"]):
        return restart_pc(), False

    # ── Veille ──
    if any(kw in t for kw in ["veille", "dors", "suspends", "mode veille"]):
        return sleep_pc(), False

    # ── Verrouillage ──
    if any(kw in t for kw in ["verrouille", "lock", "barre l'accès", "bloque l'écran"]):
        return lock_pc(), False

    # ── Mode travail ──
    if any(kw in t for kw in ["mode travail", "lance le mode travail", "je travaille"]):
        return activate_work_mode(), False

    # ── Spotify / Musique ──
    if any(kw in t for kw in ["spotify", "lance la musique", "ouvre la musique", "mets de la musique"]):
        return open_spotify(), False

    # ── Mode A.N.T.O.I.N.E ──
    if any(kw in t for kw in ["mode antoine", "séquence antoine", "active antoine"]):
        return activate_antoine_mode(), False

    # ── Calculs ──
    if any(kw in t for kw in ["calcule", "combien font", "combien fait", "résultat de",
                                "quel est le résultat", "pourcent de", "fois", "divisé par",
                                "plus", "moins", "au carré"]):
        # Exclure les faux positifs courants
        if not any(kw in t for kw in ["ouvre", "lance", "démarre", "cherche"]):
            return calculate(t), False

    # ── Mémoire : mémoriser un fait ──
    if any(kw in t for kw in ["souviens-toi que", "retiens que", "mémorise que", "n'oublie pas que"]):
        for kw in ["souviens-toi que", "retiens que", "mémorise que", "n'oublie pas que"]:
            if kw in t:
                fact = t.split(kw, 1)[1].strip()
                if fact:
                    return remember_fact(memory, fact), False
        return "Qu'est-ce que vous souhaitez que je mémorise ?", False

    # ── Mémoire : consulter ──
    if any(kw in t for kw in ["tu te souviens", "qu'est-ce que tu sais", "tes souvenirs",
                                "tu te rappelles", "rappelle-moi"]):
        return get_memories(memory), False

    # ── Météo ──
    if any(kw in t for kw in ["météo", "meteo", "temps qu'il fait", "température dehors",
                                "temperature dehors", "il pleut", "il fait beau"]):
        # Extraire la ville
        city = extract_city_from_text(t)
        return get_weather(city), False

    # ── Home Assistant : lumières ──
    if any(kw in t for kw in ["allume la lumière", "allume les lumières", "allume la lumiere",
                                "mets la lumière", "éclaire"]):
        entity = extract_ha_entity(t, default="light.all_lights")
        return ha_control_light("on", entity), False

    if any(kw in t for kw in ["éteins la lumière", "éteins les lumières", "eteins la lumiere",
                                "coupe la lumière", "coupe les lumières"]):
        entity = extract_ha_entity(t, default="light.all_lights")
        return ha_control_light("off", entity), False

    # ── Home Assistant : température ──
    if any(kw in t for kw in ["température intérieure", "temperature interieure",
                                "chauffe", "thermostat", "il fait combien chez moi"]):
        return ha_get_temperature(), False

    # ── Dossiers ──
    if any(kw in t for kw in ["ouvre le dossier", "ouvre mes documents", "ouvre le bureau",
                                "ouvre les téléchargements", "ouvre les telechargements",
                                "ouvre mes images", "ouvre mes musiques", "ouvre mes vidéos"]):
        folder = extract_folder_from_text(t)
        return _jarvis_prefix() + open_folder(folder), False

    # ── Applications ──
    if any(kw in t for kw in ["ouvre", "lance", "démarre", "démarrer", "ouvrir", "lancer"]):
        app = extract_app_from_text(t)
        if app:
            return _jarvis_prefix() + open_app(app), False

    # ── Recherche web ──
    if any(kw in t for kw in ["cherche", "recherche", "googler", "trouve sur internet"]):
        query = extract_search_query(t)
        if query:
            return web_search(query), False

    # ── Rapport système complet ──
    if any(kw in t for kw in ["rapport système", "rapport systeme", "état du système",
                                "etat du systeme", "bilan système", "bilan systeme",
                                "status système", "status systeme"]):
        return get_full_system_report(), False

    # ── Volume ──
    if any(kw in t for kw in ["coupe le son", "mute", "sourdine", "silence"]):
        return set_volume(0), False

    if any(kw in t for kw in ["monte le volume", "augmente le volume", "plus fort"]):
        return set_volume(80), False

    if any(kw in t for kw in ["baisse le volume", "diminue le volume", "moins fort"]):
        return set_volume(30), False

    _vol_match = re.search(r"volume\s+[àa]\s+(\d+)", t)
    if _vol_match or re.search(r"mets\s+le\s+volume\s+[àa]\s+(\d+)", t):
        m_vol = _vol_match or re.search(r"mets\s+le\s+volume\s+[àa]\s+(\d+)", t)
        return set_volume(int(m_vol.group(1))), False

    # ── Minuteur ──
    if any(kw in t for kw in ["annule le minuteur", "annule les minuteurs", "stop minuteur"]):
        return cancel_all_timers(), False

    _timer_match = re.search(
        r"(?:minuteur|timer|rappelle.moi\s+dans)\s+(?:de\s+)?(\d+(?:[.,]\d+)?)\s*(minute|min|heure|h)\b",
        t
    )
    if _timer_match or any(kw in t for kw in ["minuteur", "mets un timer"]):
        if _timer_match:
            val  = float(_timer_match.group(1).replace(",", "."))
            unit = _timer_match.group(2)
            minutes = val * 60 if unit.startswith("h") else val
            label_match = re.search(r"pour\s+(.+)$", t)
            label = label_match.group(1) if label_match else ""
            return start_timer(minutes, label), False

    # ── Presse-papiers ──
    if any(kw in t for kw in ["presse-papiers", "presse papiers", "clipboard",
                                "qu'est-ce que j'ai copié", "lis le presse", "contenu copié"]):
        return get_clipboard(), False

    # ── Notes vocales : enregistrer ──
    for trigger in ["note que", "note :", "prends note de", "écris que", "écris :", "mémorise que je dois", "n'oublie pas que je dois"]:
        if trigger in t:
            content = t.split(trigger, 1)[1].strip(" ?!.")
            if content:
                return save_note(content), False
    if any(kw in t for kw in ["prends note", "je veux noter"]):
        return "Que souhaitez-vous que je note, Monsieur ?", False

    # ── Notes vocales : consulter ──
    if any(kw in t for kw in ["mes notes", "lis mes notes", "quelles sont mes notes", "dernières notes", "montre mes notes"]):
        return get_notes(), False

    # ── Actualités ──
    if any(kw in t for kw in ["actualités", "actualites", "nouvelles du jour", "news", "infos du jour", "quoi de neuf dans le monde", "dernières nouvelles"]):
        return get_news(), False

    # ── Luminosité ──
    if any(kw in t for kw in ["luminosité", "luminosite", "lumineux", "éclaircis", "assombris"]):
        if any(kw in t for kw in ["monte", "augmente", "plus lumineux", "plus clair", "maximum"]):
            return set_brightness(90), False
        if any(kw in t for kw in ["baisse", "diminue", "moins lumineux", "sombre", "minimum"]):
            return set_brightness(20), False
        _lum = re.search(r"luminosit[eé]\s+[àa]\s+(\d+)", t)
        if _lum:
            return set_brightness(int(_lum.group(1))), False
        return set_brightness(60), False

    # ── Wikipedia ──
    if any(kw in t for kw in ["montre-moi", "montre moi", "ouvre wikipedia", "wikipedia sur",
                                "qu'est-ce que", "qui est", "c'est quoi"]):
        for trigger in ["montre-moi", "montre moi", "ouvre wikipedia sur", "wikipedia sur",
                        "qu'est-ce que", "qu'est ce que", "qui est", "c'est quoi"]:
            if trigger in t:
                topic = t.split(trigger, 1)[1].strip(" ?!.")
                if topic:
                    return open_wikipedia(topic), False

    # ── Fallback : IA ──
    context = build_context(memory)
    response = ask_ai(t, context)
    add_to_history(memory, t, response)
    return response, False


# ─────────────────────────────────────────────
#   UTILITAIRES D'EXTRACTION
# ─────────────────────────────────────────────

def extract_city_from_text(text: str) -> str:
    """Extrait le nom de ville d'une phrase météo."""
    patterns = [
        r"(?:météo|meteo|temps|température|temperature)\s+(?:à|a|de|en|sur|pour)?\s*([a-zA-ZÀ-ÿ\s\-]+?)(?:\s|$|\?|\.)",
        r"(?:à|a|en|de|sur|pour)\s+([a-zA-ZÀ-ÿ\s\-]+?)(?:\s|$|\?|\.)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            city = match.group(1).strip()
            if len(city) > 1 and city.lower() not in ["la", "le", "les", "il", "du", "des"]:
                return city
    return "Paris"


def extract_ha_entity(text: str, default: str) -> str:
    """Extrait l'entité Home Assistant d'une phrase (salon, chambre, cuisine...)."""
    room_map = {
        "salon":       "light.salon",
        "chambre":     "light.chambre",
        "cuisine":     "light.cuisine",
        "bureau":      "light.bureau",
        "salle de bain": "light.salle_de_bain",
        "entrée":      "light.entree",
        "couloir":     "light.couloir",
    }
    for room, entity in room_map.items():
        if room in text:
            return entity
    return default


def extract_folder_from_text(text: str) -> str:
    """Extrait le nom du dossier demandé dans la phrase."""
    for keyword in FOLDER_CATALOG:
        if keyword in text:
            return keyword
    return "bureau"


def extract_app_from_text(text: str) -> str:
    """Extrait le nom de l'application depuis la phrase."""
    trigger_words = ["ouvre", "lance", "démarre", "démarrer", "ouvrir", "lancer"]
    for trigger in trigger_words:
        if trigger in text:
            parts = text.split(trigger, 1)
            if len(parts) > 1:
                candidate = parts[1].strip()
                # Retirer les articles/prépositions courants
                for article in ["le ", "la ", "les ", "l'", "l`", "un ", "une ", "des "]:
                    if candidate.startswith(article):
                        candidate = candidate[len(article):]
                candidate = candidate.strip(" ?!.")
                if candidate:
                    return candidate
    return ""


def extract_search_query(text: str) -> str:
    """Extrait la requête de recherche depuis la phrase."""
    triggers = ["cherche ", "recherche ", "googler ", "trouve sur internet "]
    for trigger in triggers:
        if trigger in text:
            return text.split(trigger, 1)[1].strip(" ?!.")
    return text


# ─────────────────────────────────────────────
#   SÉQUENCE DE DÉMARRAGE
# ─────────────────────────────────────────────

STARTUP_BANNER = """
╔══════════════════════════════════════════════════════════════╗
║          A.N.T.O.I.N.E — V1.1                               ║
║   Autonomous Neural-Triggered Omniscient Intelligence        ║
╚══════════════════════════════════════════════════════════════╝"""


def print_startup(ha_status: str, memory_count: int):
    """Affiche la bannière de démarrage."""
    print(STARTUP_BANNER)
    print(f"   ► Chargement des modules...")
    print(f"   ► Moteurs IA : Gemini / Groq / Claude (fallback automatique)")
    print(f"   ► Reconnaissance vocale : activée (fr-FR)")
    print(f"   ► Mémoire : chargée ({memory_count} fait(s) mémorisé(s))")
    print(f"   ► Home Assistant : [{ha_status}]")
    print(f"   ► Statut : EN LIGNE")
    print()


def check_ha_status() -> str:
    """Vérifie si Home Assistant est configuré et accessible."""
    if not HA_URL or not HA_TOKEN:
        return "NON CONFIGURÉ"
    try:
        import requests
        resp = requests.get(
            f"{HA_URL.rstrip('/')}/api/",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            timeout=3,
        )
        if resp.status_code == 200:
            return "CONNECTÉ"
        return f"ERREUR {resp.status_code}"
    except Exception:
        return "INACCESSIBLE"


# ─────────────────────────────────────────────
#   BOUCLE PRINCIPALE
# ─────────────────────────────────────────────

def main():
    """Point d'entrée principal de A.N.T.O.I.N.E."""
    tts_ok  = init_tts()
    stt_ok  = init_stt()
    memory  = load_memory()
    ha_stat = check_ha_status()

    print_startup(ha_stat, len(memory.get("facts", [])))

    if not tts_ok:
        print("   [INFO] TTS non disponible. Réponses affichées en texte uniquement.")
    if not stt_ok:
        print("   [INFO] STT non disponible. Mode saisie clavier activé.")

    speak(build_startup_briefing())

    # Pre-warm: import du client IA en arrière-plan pour éviter la latence au premier appel
    import threading
    def _prewarm():
        try:
            _get_groq_client()
        except Exception:
            pass
    threading.Thread(target=_prewarm, daemon=True).start()

    running     = True
    active      = False
    active_since = 0.0
    _last_proactive = 0.0

    while running:
        try:
            # ─── Alertes proactives (toutes les 45 secondes) ───
            if time.time() - _last_proactive > 45:
                _last_proactive = time.time()
                alert = check_proactive_alerts()
                if alert:
                    speak(alert)
                    continue

            # ─── VEILLE : attente du wake word ───
            if not active:
                print("\n   [VEILLE] En attente de 'Hey Antoine'...")
                if not listen_passive():
                    continue
                speak("Je vous écoute.")
                active       = True
                active_since = time.time()
                continue

            # ─── ACTIF : timeout → retour en veille ───
            if time.time() - active_since > ACTIVE_TIMEOUT:
                speak("Je repasse en veille. Dites 'Hey Antoine' pour me réveiller.")
                active = False
                continue

            # ─── ACTIF : écoute et traitement ───
            user_text = listen()

            if not user_text:
                continue
            if user_text == "__not_understood__":
                speak("Je n'ai pas compris. Pouvez-vous répéter ?")
                continue

            active_since = time.time()
            response, should_quit = route_command(user_text, memory)
            speak(response)

            if should_quit:
                running = False

        except KeyboardInterrupt:
            speak("Arrêt manuel détecté. À bientôt.")
            running = False
        except Exception as e:
            print(f"   [ERREUR] {e}")
            speak("Je rencontre un problème technique. Veuillez réessayer.")

    print("\n   ► A.N.T.O.I.N.E hors ligne.")


if __name__ == "__main__":
    main()
