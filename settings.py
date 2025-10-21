from pathlib import Path

# App
APP_NAME = "Quiz App"


# Paths
BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_DIR = BASE_DIR / "questions"
DEFAULT_JSON = (QUESTIONS_DIR / "quiz_data.json").resolve()
CONFIG_PATH = BASE_DIR / ".quiz_app_config.json"


# Images & Fonts
IMG_MAX_W, IMG_MAX_H = 900, 420
LARGE_IMG_MAX_W, LARGE_IMG_MAX_H = 1400, 1000
FONT_Q = ("Helvetica", 18, "bold")
FONT_CHOICE = ("Helvetica", 16)
FONT_INFO = ("Helvetica", 12, "bold")
