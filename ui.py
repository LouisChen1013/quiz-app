import json
import string
from pathlib import Path
import tkinter as tk
from tkinter import ttk, Menu, messagebox
from tkinter.scrolledtext import ScrolledText
from ttkbootstrap import Style
from PIL import Image, ImageTk

import settings
from model import QuizModel, save_json


class ScrollableFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")

        self.inner = ttk.Frame(self.canvas)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

    def _bind_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_win)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_up)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_down)

    def _unbind_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_inner_configure(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas.itemconfigure(self._win, width=e.width)

    def _on_mousewheel_win(self, e):
        delta = e.delta
        step = -1 if delta > 0 else 1
        self.canvas.yview_scroll(step, "units")

    def _on_mousewheel_up(self, _):
        self.canvas.yview_scroll(-3, "units")

    def _on_mousewheel_down(self, _):
        self.canvas.yview_scroll(3, "units")

    def scroll_to_top(self):
        self.canvas.yview_moveto(0.0)


class QuizApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(settings.APP_NAME)
        self.root.geometry("960x720")
        self.style = Style(theme="flatly")
        self.center_window()

        # 掃描題庫檔案
        assets_base = settings.DEFAULT_JSON.parent
        quiz_files = sorted(assets_base.glob("quiz_data_*.json")) or [
            settings.DEFAULT_JSON
        ]
        self.quiz_files = quiz_files

        # Model
        self.model = QuizModel(self.quiz_files)

        # UI 狀態
        self.original_img = None
        self.img_tk = None
        self.selected_var = tk.StringVar(value="")
        self.multi_vars: dict[str, tk.BooleanVar] = {}

        # ===== 版面 =====
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)
        self.root.columnconfigure(0, weight=1)

        outer = ttk.Frame(self.root, padding=(16, 16, 16, 8))
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        card = ttk.Frame(outer, padding=20, style="Card.TFrame")
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)
        card.rowconfigure(1, weight=0)
        card.rowconfigure(2, weight=0)

        # 上方可捲動區
        self.scroll_area = ScrollableFrame(card)
        self.scroll_area.grid(row=0, column=0, sticky="nsew")
        content = self.scroll_area.inner
        content.columnconfigure(0, weight=1)

        # 題目
        self.qs_label = ttk.Label(
            content,
            text="",
            anchor="w",
            justify="left",
            wraplength=900,
            font=settings.FONT_Q,
        )
        self.qs_label.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # 多選提示
        self.multi_hint = ttk.Label(
            content,
            text="Select all that apply",
            foreground="#0d6efd",
            font=settings.FONT_INFO,
        )
        self.multi_hint.grid(row=1, column=0, sticky="w", pady=(0, 8))
        self.multi_hint.grid_remove()

        # 圖片
        self.img_label = ttk.Label(content)
        self.img_label.grid(row=2, column=0, sticky="n", pady=(0, 12))
        self.img_label.bind("<Button-1>", self.show_large_image)

        # 選項
        self.choices_frame = ttk.Frame(content)
        self.choices_frame.grid(row=3, column=0, sticky="ew")
        self.choice_widgets: list[tk.Widget] = []

        # 回饋
        self.feedback_label = ttk.Label(
            content, text="", justify="center", font=("Helvetica", 16)
        )
        self.feedback_label.grid(row=4, column=0, pady=(12, 8))

        # 狀態列
        status = ttk.Frame(card)
        status.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        status.columnconfigure(0, weight=1)

        self.progress_var = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(status, maximum=1, variable=self.progress_var)
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.score_label = ttk.Label(status, text=f"Score: 0/1", font=("Helvetica", 12))
        self.score_label.grid(row=0, column=1)

        # 底部工具列
        footer = ttk.Frame(card)
        footer.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        footer.columnconfigure(0, weight=0)
        footer.columnconfigure(1, weight=1)
        footer.columnconfigure(2, weight=0)

        left_bar = ttk.Frame(footer)
        left_bar.grid(row=0, column=0, sticky="w")

        self.options_btn = ttk.Menubutton(
            left_bar, text="Options", bootstyle="secondary"
        )
        self.options_btn.pack(side="left", padx=(0, 6))
        self.options_menu = Menu(self.options_btn, tearoff=0)
        self.populate_options_menu()
        self.options_btn["menu"] = self.options_menu

        self.desc_btn = ttk.Button(
            left_bar,
            text="Description",
            command=self.show_description,
            bootstyle="info",
        )
        self.desc_btn.pack(side="left", padx=6)

        self.goto_btn = ttk.Button(
            left_bar,
            text="Go to Q",
            command=self.show_goto_dialog,
            bootstyle="secondary",
        )
        self.goto_btn.pack(side="left", padx=6)

        right_bar = ttk.Frame(footer)
        right_bar.grid(row=0, column=2, sticky="e")

        self.submit_btn = ttk.Button(
            right_bar,
            text="Submit (Enter)",
            command=self.check_answer,
            bootstyle="primary",
        )
        self.submit_btn.pack(side="left", padx=6)

        btn_width = 10
        self.prev_btn = ttk.Button(
            right_bar, text="Previous (P)", command=self.prev_question, width=btn_width
        )
        self.prev_btn.pack(side="left", padx=6)

        self.next_btn = ttk.Button(
            right_bar, text="Next (N)", command=self.next_question, width=btn_width
        )
        self.next_btn.pack(side="left", padx=6)

        self.quit_btn = ttk.Button(
            right_bar, text="Quit", command=self.root.destroy, bootstyle="danger"
        )
        self.quit_btn.pack(side="left", padx=6)

        self.result_btn = ttk.Button(
            right_bar, text="Result", command=self.show_result, bootstyle="secondary"
        )
        self.result_btn.pack(side="left", padx=6)

        # 熱鍵
        self.root.bind("<Return>", lambda e: self.check_answer())
        self.root.bind("<n>", lambda e: self.next_question())
        self.root.bind("<N>", lambda e: self.next_question())
        self.root.bind("<p>", lambda e: self.prev_question())
        self.root.bind("<P>", lambda e: self.prev_question())
        self.root.bind("<Control-s>", lambda e: self.show_result())
        self.root.bind("<Control-g>", lambda e: self.show_goto_dialog())
        self.root.bind("<Control-d>", lambda e: self.show_description())
        for c in string.ascii_lowercase[:26]:
            self.root.bind(f"<{c}>", lambda e, l=c.upper(): self.pick(l))
            self.root.bind(f"<{c.upper()}>", lambda e, l=c.upper(): self.pick(l))
        self.root.bind("<Configure>", self.on_resize)

        # 載入設定與題庫
        cfg = self.load_config()
        last_file = cfg.get("last_quiz_file")
        try:
            if last_file and Path(last_file).exists():
                self.model.load(Path(last_file))
            else:
                self.model.load(self.quiz_files[0])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load quiz file:\n{e}")
            self.model.data = []

        self.model.set_shuffle_choices(cfg.get("shuffle_choices", False))
        if cfg.get("shuffle_questions", False):
            self.model.set_shuffle_questions(True)
        self._cfg_cache = cfg

        self.refresh_progress_ui()
        self.show_question()

    # ---------- 設定檔 ----------
    def load_config(self) -> dict:
        if settings.CONFIG_PATH.exists():
            try:
                return json.loads(settings.CONFIG_PATH.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save_config(self):
        data = {
            "last_quiz_file": str(self._cfg_cache.get("last_quiz_file")),
            "shuffle_questions": self.model.shuffle_questions,
            "shuffle_choices": self.model.shuffle_choices,
        }
        save_json(settings.CONFIG_PATH, data)

    # ---------- 選單 ----------
    def populate_options_menu(self):
        self.options_menu.delete(0, "end")
        current = getattr(self, "_cfg_cache", {}).get("last_quiz_file")
        for qf in self.quiz_files:
            name = qf.stem

            def _cmd(p=qf):
                self.load_quiz_file(p)

            if current and str(qf) == str(current):
                self.options_menu.add_command(label=f"✓ {name}", command=_cmd)
            else:
                self.options_menu.add_command(label=name, command=_cmd)
        self.options_menu.add_separator()
        self.options_menu.add_command(
            label="Start Sample Test", command=self.start_test_mode
        )
        self.options_menu.add_separator()
        self.shuffle_q_var = tk.BooleanVar(
            value=getattr(self, "_cfg_cache", {}).get("shuffle_questions", False)
        )
        self.shuffle_c_var = tk.BooleanVar(
            value=getattr(self, "_cfg_cache", {}).get("shuffle_choices", False)
        )
        self.options_menu.add_checkbutton(
            label="Shuffle Questions",
            variable=self.shuffle_q_var,
            onvalue=True,
            offvalue=False,
            command=self.apply_shuffle_mode,
        )
        self.options_menu.add_checkbutton(
            label="Shuffle Choices",
            variable=self.shuffle_c_var,
            onvalue=True,
            offvalue=False,
            command=self.on_toggle_shuffle_choices,
        )

    # ---------- 基本控制 ----------
    def refresh_progress_ui(self):
        total = self.model.num_questions() or 1
        self.progress.configure(maximum=total)
        self.progress_var.set(
            self.model.current_index + 1 if self.model.num_questions() else 0
        )
        self.score_label.config(text=f"Score: {self.model.score()}/{total}")

    def load_quiz_file(self, file_path: Path):
        try:
            self.model.load(file_path)
            self._cfg_cache["last_quiz_file"] = str(file_path)
            self.populate_options_menu()
            self.refresh_progress_ui()
            self.show_question()
            self.save_config()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load quiz file:\n{e}")

    def apply_shuffle_mode(self):
        flag = self.shuffle_q_var.get()
        if flag:
            self.model.set_shuffle_questions(True)
        else:
            last = Path(self._cfg_cache.get("last_quiz_file", str(self.quiz_files[0])))
            self.model.load(last)
            self.model.set_shuffle_choices(self.shuffle_c_var.get())
        self.refresh_progress_ui()
        self.show_question()
        self._cfg_cache["shuffle_questions"] = flag
        self.save_config()

    def on_toggle_shuffle_choices(self):
        flag = self.shuffle_c_var.get()
        self.model.set_shuffle_choices(flag)
        self.show_question()
        self._cfg_cache["shuffle_choices"] = flag
        self.save_config()

    def on_resize(self, _=None):
        wrap = max(560, self.root.winfo_width() - 120)
        self.qs_label.configure(wraplength=wrap)
        for w in self.choice_widgets:
            try:
                w.configure(wraplength=wrap)
            except tk.TclError:
                pass
        if self.original_img is not None:
            self.display_image(self.original_img)

    def pick(self, letter):
        letter = (letter or "").strip().upper()
        if not self.choice_widgets:
            return
        is_multi = self.model.is_multi(self.model.current_index)
        if is_multi:
            var = self.multi_vars.get(letter)
            if var is not None:
                var.set(not var.get())
        else:
            self.selected_var.set(letter)

    def jump_to_question(self, idx: int, result_window=None):
        self.model.current_index = idx
        self.show_question()
        if result_window:
            result_window.destroy()

    # ---------- 顯示題目 ----------
    def show_question(self):
        if self.model.num_questions() == 0:
            self.qs_label.config(text="No questions.")
            return

        qidx = self.model.current_index
        q = self.model.question(qidx)
        num_choices = len(q.get("choices", []))
        is_multi = self.model.is_multi(qidx)

        self.multi_vars = {
            L: tk.BooleanVar(value=False) for L in string.ascii_uppercase[:num_choices]
        }
        self.selected_var.set("")
        prev = self.model.answers.get(qidx)

        self.feedback_label.config(text="", foreground="")
        self.progress_var.set(qidx + 1)
        self.qs_label.config(text=f"{q.get('id', qidx + 1)}. {q['question']}")
        self.multi_hint.grid() if is_multi else self.multi_hint.grid_remove()

        img_path = self.model.image_path(qidx)
        if img_path and img_path.exists():
            try:
                self.original_img = Image.open(img_path)
                self.display_image(self.original_img)
                self.img_label.config(cursor="hand2")
            except Exception:
                self.original_img = None
                self.img_label.config(image="", text="", cursor="")
        else:
            self.original_img = None
            self.img_label.config(image="", text="", cursor="")

        for w in self.choice_widgets:
            w.destroy()
        self.choice_widgets.clear()

        choice_pairs = self.model.get_choice_pairs(qidx)
        letters_all = list(string.ascii_uppercase)
        disp_letters = letters_all[: len(choice_pairs)]

        display_to_orig = {}
        orig_to_display = {}

        for i, (orig_letter, text) in enumerate(choice_pairs):
            disp_letter = disp_letters[i]
            display_to_orig[disp_letter] = orig_letter
            orig_to_display[orig_letter] = disp_letter

            display_text = f"{disp_letter}. {text}"
            if is_multi:
                var = self.multi_vars.get(disp_letter) or tk.BooleanVar(value=False)
                self.multi_vars[disp_letter] = var
                if isinstance(prev, set) and orig_letter in prev:
                    var.set(True)
                cb = tk.Checkbutton(
                    self.choices_frame,
                    text=display_text,
                    variable=var,
                    anchor="w",
                    justify="left",
                    wraplength=900,
                    font=settings.FONT_CHOICE,
                    padx=12,
                    pady=10,
                    bg="white",
                    relief="flat",
                    onvalue=True,
                    offvalue=False,
                    selectcolor="#eef5ff",
                )
                cb.pack(fill="x", pady=6)
                self.choice_widgets.append(cb)
            else:
                if isinstance(prev, str) and prev == orig_letter:
                    self.selected_var.set(disp_letter)
                rb = tk.Radiobutton(
                    self.choices_frame,
                    text=display_text,
                    variable=self.selected_var,
                    value=disp_letter,
                    anchor="w",
                    justify="left",
                    wraplength=900,
                    font=settings.FONT_CHOICE,
                    padx=12,
                    pady=10,
                    indicatoron=True,
                    bg="white",
                    relief="flat",
                    selectcolor="#eef5ff",
                )
                rb.pack(fill="x", pady=6)
                self.choice_widgets.append(rb)

        self.model.choice_letter_maps[qidx] = {
            "display_to_orig": display_to_orig,
            "orig_to_display": orig_to_display,
        }

        self.scroll_area.scroll_to_top()
        self.refresh_progress_ui()

    # ---------- 圖片顯示 ----------
    def display_image(self, pil_img):
        w, h = pil_img.size
        max_w = min(max(520, self.root.winfo_width() - 120), settings.IMG_MAX_W)
        max_h = settings.IMG_MAX_H
        scale = min(max_w / w, max_h / h)
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        img_resized = pil_img.resize((new_w, new_h))
        self.img_tk = ImageTk.PhotoImage(img_resized)
        self.img_label.config(image=self.img_tk)
        self.root.after(0, self.scroll_area._on_inner_configure, None)

    def show_large_image(self, _=None):
        if not self.original_img:
            return
        top = tk.Toplevel(self.root)
        top.title("Image Preview")
        w, h = self.original_img.size
        scale = min(settings.LARGE_IMG_MAX_W / w, settings.LARGE_IMG_MAX_H / h, 1.0)
        img_large = self.original_img.resize((int(w * scale), int(h * scale)))
        img_large_tk = ImageTk.PhotoImage(img_large)
        lbl = ttk.Label(top, image=img_large_tk)
        lbl.image = img_large_tk
        lbl.pack(padx=10, pady=10)

    # ---------- 作答 ----------
    def check_answer(self):
        if self.model.num_questions() == 0:
            return
        is_multi = self.model.is_multi(self.model.current_index)
        if is_multi:
            picked_display = {k for k, v in self.multi_vars.items() if v.get()}
        else:
            picked_display = self.selected_var.get()
        result, payload = self.model.grade_current(picked_display)
        if result is None:
            messagebox.showinfo("提示", payload)
            return
        if result:
            self.feedback_label.config(text="Correct!", foreground="green")
        else:
            if is_multi:
                self.feedback_label.config(
                    text=f"Incorrect! Correct answers: {payload}", foreground="red"
                )
            else:
                self.feedback_label.config(
                    text=f"Incorrect! Correct answer: {payload}", foreground="red"
                )
        self.refresh_progress_ui()

    def next_question(self):
        if self.model.current_index + 1 < self.model.num_questions():
            self.model.current_index += 1
            self.show_question()

    def prev_question(self):
        if self.model.current_index > 0:
            self.model.current_index -= 1
            self.show_question()

    # ---------- 解說 ----------
    def show_description(self):
        if self.model.num_questions() == 0:
            return
        q = self.model.question(self.model.current_index)
        desc = q.get("description") or "No description provided."

        top = tk.Toplevel(self.root)
        top.title("Description")
        top.geometry("700x500")
        top.bind("<Escape>", lambda e: top.destroy())

        text_widget = ScrolledText(top, wrap="word", font=("Consolas", 12))
        text_widget.insert("1.0", desc)
        text_widget.configure(state="disabled")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(top, text="Close", command=top.destroy).pack(pady=6)

    # ---------- 跳題 ----------
    def show_goto_dialog(self):
        if self.model.num_questions() == 0:
            return
        ids = [q.get("id", idx + 1) for idx, q in enumerate(self.model.data)]
        min_id, max_id = min(ids), max(ids)

        top = tk.Toplevel(self.root)
        top.title("Go to Question")
        top.geometry("300x150")
        top.resizable(False, False)
        top.bind("<Escape>", lambda e: top.destroy())
        top.update_idletasks()
        w = top.winfo_width()
        h = top.winfo_height()
        ws = top.winfo_screenwidth()
        hs = top.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        top.geometry(f"{w}x{h}+{x}+{y}")

        ttk.Label(top, text=f"Enter question number ({min_id}-{max_id}):").pack(
            pady=(20, 6)
        )
        entry_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=entry_var, font=("Helvetica", 14))
        entry.pack(pady=6)
        entry.focus()

        def go_to_question():
            val = entry_var.get().strip()
            if not val.isdigit():
                messagebox.showerror("Error", "Please enter a valid number.")
                return
            qid = int(val)
            if qid in ids:
                idx = ids.index(qid)
                self.model.current_index = idx
                self.show_question()
                top.destroy()
            else:
                messagebox.showerror(
                    "Error", f"Number out of range ({min_id}-{max_id})."
                )

        ttk.Button(top, text="Go", command=go_to_question).pack(pady=10)
        entry.bind("<Return>", lambda e: go_to_question())

    # ---------- 成績結果 ----------
    def show_result(self):
        if self.model.num_questions() == 0:
            return
        top = tk.Toplevel(self.root)
        top.title("Quiz Result")
        top.geometry("460x360")
        top.bind("<Escape>", lambda e: top.destroy())

        canvas = tk.Canvas(top)
        vbar = ttk.Scrollbar(top, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        frame = ttk.Frame(canvas)
        frame_id = canvas.create_window((0, 0), window=frame, anchor="nw")

        def on_canvas_configure(e):
            canvas.itemconfigure(frame_id, width=e.width)

        canvas.bind("<Configure>", on_canvas_configure)

        def on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(-1 * (event.delta // 120), "units")
            else:
                if event.num == 4:
                    canvas.yview_scroll(-3, "units")
                elif event.num == 5:
                    canvas.yview_scroll(3, "units")

        canvas.bind("<Enter>", lambda e: _bind_result_mousewheel())
        canvas.bind("<Leave>", lambda e: _unbind_result_mousewheel())

        def _bind_result_mousewheel():
            canvas.bind_all("<MouseWheel>", on_mousewheel)
            canvas.bind_all("<Button-4>", on_mousewheel)
            canvas.bind_all("<Button-5>", on_mousewheel)

        def _unbind_result_mousewheel():
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        def on_frame_configure(_):
            canvas.configure(scrollregion=canvas.bbox("all"))

        frame.bind("<Configure>", on_frame_configure)

        total = self.model.num_questions()
        wrong_items = []
        for idx, q in enumerate(self.model.data):
            correct_ans = q.get("answer", "")
            user_ans = self.model.answers.get(idx)
            is_correct = self.model.correct_map.get(idx, False)
            if not is_correct:
                wrong_items.append((q.get("id", idx + 1), idx))

        score = total - len(wrong_items)
        percent = (score / total * 100) if total else 0
        ttk.Label(frame, text=f"Score: {score}/{total} ({percent:.1f}%)").pack(
            anchor="w", pady=(0, 8)
        )

        if wrong_items:
            ttk.Label(frame, text="Wrong questions:").pack(anchor="w")
            buttons_frame = ttk.Frame(frame)
            buttons_frame.pack(anchor="w")
            max_per_row = 6
            for i, (qid, idx) in enumerate(wrong_items):
                row = i // max_per_row
                col = i % max_per_row
                btn = ttk.Button(
                    buttons_frame,
                    text=str(qid),
                    width=4,
                    command=lambda i=idx, w=top: self.jump_to_question(i, w),
                )
                btn.grid(row=row, column=col, padx=2, pady=2)
        else:
            ttk.Label(frame, text="All correct! 🎉").pack(anchor="w", pady=(0, 8))

        ttk.Button(frame, text="Close", command=top.destroy).pack(pady=6)

    # ---------- 置中 ----------
    def center_window(self, width=1000, height=700):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    # ---------- 測驗模式 ----------
    def start_test_mode(self):
        try:
            self.model.start_test_mode()
            self.refresh_progress_ui()
            self.show_question()
            messagebox.showinfo(
                "Test Mode", "已隨機生成 50 題考卷（包含 quiz4 至少 12 題）"
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
