"""
Lanceur silencieux — A.N.T.O.I.N.E V1.1
Double-cliquer ce fichier pour démarrer Antoine sans fenêtre noire.
Les logs sont écrits dans antoine.log (même dossier).
"""
import sys
from pathlib import Path

# Redirige tous les prints vers un fichier log (pas de console disponible)
_log = open(Path(__file__).parent / "antoine.log", "w", encoding="utf-8", buffering=1)
sys.stdout = _log
sys.stderr = _log

sys.path.insert(0, str(Path(__file__).parent))
from antoine import main
main()
