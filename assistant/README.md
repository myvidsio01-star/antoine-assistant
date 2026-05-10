# A.N.T.O.I.N.E V1.0
**Autonomous Neural-Triggered Omniscient Intelligence**

Assistant vocal personnel en français pour Windows, inspiré du projet JARVIS de TechEnClair.

---

## Prérequis

- **Python 3.10 ou plus récent** — [Télécharger ici](https://python.org)
- **Un microphone** connecté à votre PC
- **Une connexion internet** pour les fonctions IA et météo
- **Au moins une clé API** parmi : Gemini, Groq ou Claude (Anthropic)

---

## Installation

### Méthode 1 — Installation automatique (recommandée)
Double-cliquez sur `setup.bat` et suivez les instructions.

### Méthode 2 — Installation manuelle
```
pip install -r requirements.txt
copy .env.example .env
```

### Problème avec PyAudio sur Windows ?
Si PyAudio échoue à l'installation, utilisez l'une de ces solutions :

**Solution A :**
```
pip install pipwin
pipwin install pyaudio
```

**Solution B :** Téléchargez le fichier `.whl` correspondant à votre version Python sur :
https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

Puis installez-le :
```
pip install PyAudio-0.2.xx-cpXX-cpXX-win_amd64.whl
```

---

## Configuration

Ouvrez le fichier `.env` (créé automatiquement depuis `.env.example`) et renseignez vos clés :

```
GEMINI_API_KEY=votre_clé_ici
GROQ_API_KEY=votre_clé_ici
ANTHROPIC_API_KEY=votre_clé_ici
```

### Où obtenir les clés API (toutes gratuites au départ) :
| Service | Lien | Plan gratuit |
|---------|------|-------------|
| Gemini  | https://aistudio.google.com/apikey | Oui |
| Groq    | https://console.groq.com           | Oui |
| Claude  | https://console.anthropic.com      | Oui (limité) |

### Domotique Home Assistant (optionnel)
```
HA_URL=http://192.168.1.X:8123
HA_TOKEN=votre_long_lived_access_token
```

---

## Lancement

### Méthode rapide
Double-cliquez sur `run.bat`

### Méthode manuelle
```
python antoine.py
```

---

## Commandes disponibles

### Informations système (pas besoin d'internet)
| Ce que vous dites | Action |
|-------------------|--------|
| "Quelle heure est-il ?" | Affiche l'heure actuelle |
| "Quel jour sommes-nous ?" | Affiche la date |
| "Quel est le niveau de batterie ?" | Niveau de charge |
| "Montre-moi les stats du processeur" | CPU et RAM |

### Captures et fichiers
| Ce que vous dites | Action |
|-------------------|--------|
| "Prends une capture d'écran" | Sauvegarde sur le Bureau |
| "Ouvre le Bureau" | Ouvre le dossier Bureau |
| "Ouvre mes Documents" | Ouvre le dossier Documents |
| "Ouvre mes Téléchargements" | Ouvre le dossier Téléchargements |

### Applications
| Ce que vous dites | Application ouverte |
|-------------------|---------------------|
| "Ouvre Chrome" | Google Chrome |
| "Lance Firefox" | Mozilla Firefox |
| "Démarre Spotify" | Spotify |
| "Ouvre Discord" | Discord |
| "Lance VSCode" | Visual Studio Code |
| "Ouvre le Notepad" | Bloc-notes Windows |
| "Lance la calculatrice" | Calculatrice Windows |
| "Ouvre le gestionnaire de tâches" | Gestionnaire de tâches |
| "Lance Steam" | Steam |
| "Ouvre OBS" | OBS Studio |
| "Lance Teams" | Microsoft Teams |
| "Ouvre WhatsApp" | WhatsApp Desktop |

### Contrôle du PC
| Ce que vous dites | Action |
|-------------------|--------|
| "Éteins le PC" | Arrêt dans 10 secondes |
| "Redémarre le PC" | Redémarrage dans 10 secondes |
| "Mets le PC en veille" | Mode veille |
| "Verrouille la session" | Écran de verrouillage |

### Calculs (pas besoin d'internet)
| Ce que vous dites | Exemple |
|-------------------|---------|
| "Calcule X fois Y" | "Calcule 12 fois 8" |
| "X pourcent de Y" | "15 pourcent de 340" |
| "Combien font X plus Y" | "Combien font 150 plus 75" |
| "X divisé par Y" | "100 divisé par 4" |

### Météo (internet requis — gratuit, sans clé)
| Ce que vous dites | Action |
|-------------------|--------|
| "Météo à Paris" | Météo actuelle à Paris |
| "Quel temps fait-il à Lyon ?" | Météo à Lyon |
| "Température à Marseille" | Météo à Marseille |

### Mémoire
| Ce que vous dites | Action |
|-------------------|--------|
| "Souviens-toi que mon chat s'appelle Milo" | Mémorise le fait |
| "Tu te souviens de quoi ?" | Récite les faits mémorisés |
| "Mémorise que j'ai rendez-vous lundi" | Mémorise le fait |

### Domotique (Home Assistant requis)
| Ce que vous dites | Action |
|-------------------|--------|
| "Allume la lumière du salon" | Allume le salon |
| "Éteins les lumières" | Éteint toutes les lumières |
| "Quelle est la température chez moi ?" | Lit le thermostat |

### Recherche web
| Ce que vous dites | Action |
|-------------------|--------|
| "Cherche les actualités du jour" | Ouvre Google |
| "Recherche Python tutoriel" | Ouvre Google |

### Modes spéciaux
| Ce que vous dites | Action |
|-------------------|--------|
| "Mode travail" | Ouvre le Bloc-notes |
| "Mode Antoine" | Séquence d'activation spéciale |
| "Mets de la musique" | Ouvre Spotify |

### Quitter
| Ce que vous dites | Action |
|-------------------|--------|
| "Stop", "Au revoir", "Quitte" | Arrête A.N.T.O.I.N.E |

---

## Fonctionnement de l'IA

A.N.T.O.I.N.E utilise un système de **fallback automatique** entre trois moteurs IA :

1. **Gemini 1.5 Flash** (Google) — Essayé en premier si la clé est configurée
2. **Groq llama-3.3-70b-versatile** — Utilisé si Gemini échoue ou n'est pas configuré
3. **Claude Haiku** (Anthropic) — Dernier recours

Si aucun moteur n'est disponible, A.N.T.O.I.N.E vous informe et vous invite à configurer une clé API.

---

## Dépannage

### "PyAudio n'est pas installé"
Voir la section Installation ci-dessus pour les solutions PyAudio.

### "pyttsx3 n'est pas installé"
```
pip install pyttsx3
```

### "Aucune clé API configurée"
Ouvrez le fichier `.env` et ajoutez au moins une clé API.

### Le microphone n'est pas reconnu
- Vérifiez que votre micro est branché et défini comme périphérique par défaut dans Windows
- Allez dans Paramètres > Système > Son > Entrée

### La voix française n'est pas disponible
- Allez dans Paramètres > Heure et langue > Parole
- Téléchargez la voix "Hortense" (français France)

### A.N.T.O.I.N.E ne comprend pas ma voix
- Parlez clairement et attendez le signal "[ÉCOUTE]"
- Réduisez les bruits de fond
- Si la connexion est lente, la reconnaissance peut être plus lente

### Mode texte (sans micro)
Si le microphone n'est pas disponible, A.N.T.O.I.N.E passe automatiquement en mode saisie clavier. Vous pouvez taper vos commandes directement.

---

## Structure des fichiers

```
assistant/
├── antoine.py           # Script principal
├── antoine_memory.json  # Mémoire (créé automatiquement)
├── requirements.txt     # Dépendances Python
├── .env                 # Vos clés API (à créer depuis .env.example)
├── .env.example         # Modèle de configuration
├── setup.bat            # Installation automatique
├── run.bat              # Lancement rapide
└── README.md            # Ce fichier
```

---

*A.N.T.O.I.N.E V1.0 — Inspiré du projet JARVIS de TechEnClair*
