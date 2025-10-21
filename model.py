import json
import random
import string
from pathlib import Path
import settings


def load_json(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(p: Path, data: dict):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def norm_letter(ch: str) -> str:
    return (ch or "").strip().upper()


class QuizModel:
    def __init__(self, file_paths):
        self.file_paths = file_paths
        self.assets_base = (
            file_paths[0].parent if file_paths else settings.DEFAULT_JSON.parent
        )
        self.data = []  # list[dict]
        self.current_index = 0
        self.answers = {}  # idx -> set[str] 或 str（原始字母）
        self.correct_map = {}
        self.shuffled_choices = {}
        self.choice_letter_maps = {}
        self.shuffle_questions = False
        self.shuffle_choices = False

    def available_quiz_files(self):
        return self.file_paths

    def load(self, file_path: Path):
        self.data = load_json(file_path)
        self.assets_base = file_path.parent
        self.current_index = 0
        self.answers.clear()
        self.correct_map.clear()
        self.shuffled_choices.clear()
        self.choice_letter_maps.clear()

    def start_test_mode(self):
        all_quizzes = {qf.stem: load_json(qf) for qf in self.file_paths}
        quiz4_key = next((k for k in all_quizzes if "quiz_data_4" in k), None)
        if not quiz4_key:
            raise RuntimeError("找不到 quiz_data_4.json，無法進入 Test 模式")
        quiz4_data = all_quizzes[quiz4_key]
        if len(quiz4_data) < 12:
            raise RuntimeError(f"{quiz4_key} 題目不足 12 題")

        selected = random.sample(quiz4_data, 12)
        other_pool = [q for k, v in all_quizzes.items() if k != quiz4_key for q in v]
        remaining = 50 - 12
        if len(other_pool) < remaining:
            raise RuntimeError("其他 quiz 題目數不足以補齊 50 題")
        selected.extend(random.sample(other_pool, remaining))
        random.shuffle(selected)

        self.data = selected
        self.current_index = 0
        self.answers.clear()
        self.correct_map.clear()
        self.shuffled_choices.clear()
        self.choice_letter_maps.clear()

    def num_questions(self):
        return len(self.data)

    def question(self, idx: int):
        return self.data[idx]

    def is_multi(self, idx: int) -> bool:
        ans = self.data[idx].get("answer", "")
        return isinstance(ans, list)

    def image_path(self, idx: int):
        img_field = self.data[idx].get("image")
        if not img_field:
            return None
        p = Path(img_field)
        return p if p.is_absolute() else (self.assets_base / p)

    def normalize_choices(self, idx: int):
        q = self.data[idx]
        raw = q["choices"].copy()
        letters = list(string.ascii_uppercase)
        norm = []
        for i, txt in enumerate(raw):
            letter0 = letters[i]
            t = str(txt).strip()
            if len(t) >= 2 and t[1] == "." and t[0].upper() in letters:
                t = t[2:].strip()
            norm.append((letter0, t))
        return norm

    def get_choice_pairs(self, idx: int):
        if self.shuffle_choices:
            if idx not in self.shuffled_choices:
                base = self.normalize_choices(idx)
                self.shuffled_choices[idx] = random.sample(base, len(base))
            return self.shuffled_choices[idx]
        else:
            return self.normalize_choices(idx)

    def set_shuffle_questions(self, flag: bool):
        self.shuffle_questions = flag
        if flag:
            self.data = random.sample(self.data, len(self.data))
        self.answers.clear()
        self.correct_map.clear()
        self.shuffled_choices.clear()
        self.choice_letter_maps.clear()
        self.current_index = 0

    def set_shuffle_choices(self, flag: bool):
        self.shuffle_choices = flag
        self.shuffled_choices.pop(self.current_index, None)
        self.choice_letter_maps.pop(self.current_index, None)

    def grade_current(self, picked_display_letters: set | str):
        idx = self.current_index
        maps = self.choice_letter_maps.get(idx, {})
        d2o = maps.get("display_to_orig", {})
        o2d = maps.get("orig_to_display", {})
        q = self.data[idx]
        correct_raw = q.get("answer", "")

        if isinstance(correct_raw, list):
            if not picked_display_letters:
                return None, "請至少選擇一個選項。"
            picked_display_letters = set(norm_letter(x) for x in picked_display_letters)
            picked_orig = {d2o.get(L, L) for L in picked_display_letters}
            self.answers[idx] = picked_orig
            correct_set = set(norm_letter(s) for s in correct_raw)
            is_correct = picked_orig == correct_set
            self.correct_map[idx] = is_correct
            disp_correct = sorted(o2d.get(L, L) for L in correct_set)
            return is_correct, ", ".join(disp_correct)
        else:
            chosen_display = norm_letter(picked_display_letters)
            if not chosen_display:
                return None, "請先選擇一個選項。"
            picked_orig = d2o.get(chosen_display, chosen_display)
            self.answers[idx] = picked_orig
            correct = norm_letter(str(correct_raw))
            is_correct = picked_orig == correct
            self.correct_map[idx] = is_correct
            disp_correct = o2d.get(correct, correct)
            return is_correct, disp_correct

    def score(self):
        return sum(1 for v in self.correct_map.values() if v)
