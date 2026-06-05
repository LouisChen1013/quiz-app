# settings.py

from pathlib import Path

# App
APP_NAME = "Quiz App"

# Paths
BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_DIR = BASE_DIR / "questions"

# 考試類型資料夾映射
EXAM_DIRS = {
    "PCA": QUESTIONS_DIR / "PCA",
    "PCS": QUESTIONS_DIR / "PCS",
    "TFA": QUESTIONS_DIR / "TFA",
}

# 預設考試（可改 "PCA" 或 "PCS" OR TFA）
DEFAULT_EXAM = "TFA"

# DEFAULT_JSON：指到預設考試底下
DEFAULT_JSON = (EXAM_DIRS[DEFAULT_EXAM] / "quiz_data.json").resolve()

CONFIG_PATH = BASE_DIR / ".quiz_app_config.json"

# Images & Fonts
IMG_MAX_W, IMG_MAX_H = 900, 420
LARGE_IMG_MAX_W, LARGE_IMG_MAX_H = 1400, 1000
FONT_Q = ("Helvetica", 18, "bold")
FONT_CHOICE = ("Helvetica", 16)
FONT_INFO = ("Helvetica", 12, "bold")
