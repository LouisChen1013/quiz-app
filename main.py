import tkinter as tk
import ui


def main():
    root = tk.Tk()
    app = ui.QuizApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.save_config(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
