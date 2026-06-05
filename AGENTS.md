# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python desktop quiz application built with Tkinter and `ttkbootstrap`.

- `main.py`: application entry point.
- `ui.py`: windows, widgets, navigation, and user interactions.
- `model.py`: question loading, shuffling, grading, and scoring logic.
- `settings.py`: exam mappings, paths, image sizes, and font constants.
- `questions/<EXAM>/quiz_data_*.json`: question banks for PCA, PCS, and TFA exams.
- `images/`: shared images referenced by question JSON.
- `.quiz_app_config.json`: saved local UI state; avoid unrelated changes to it.

Question objects should retain the existing schema: `id`, `question`, `choices`, `answer`, optional `image`, and optional `description`. Use a string answer for single-choice questions and a list for multiple-choice questions.

## Build, Test, and Development Commands

Create and activate a Python 3.9+ virtual environment, then run:

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

There is no build step or automated test suite. Before submitting changes, perform basic validation:

```bash
python3 -m compileall main.py model.py settings.py ui.py
python3 -m json.tool questions/PCA/quiz_data_1.json >/dev/null
```

Launch the app and manually verify quiz loading, answer grading, navigation, shuffling, images, and Test mode when relevant.

## Coding Style & Naming Conventions

Follow existing Python style: four-space indentation, `snake_case` functions and variables, `PascalCase` classes, and uppercase constants in `settings.py`. Keep UI behavior in `ui.py` and reusable quiz logic in `model.py`. Use `pathlib.Path` for filesystem paths and UTF-8 for JSON. Preserve the established two-space JSON indentation and `quiz_data_<number>.json` naming pattern.

## Commit & Pull Request Guidelines

Recent commits use short Conventional Commit-style subjects, such as `feat: added PCS option`. Use an imperative subject with an appropriate prefix (`feat:`, `fix:`, `docs:`), and keep each commit focused.

Pull requests should explain the behavior changed, identify affected exam banks or modules, and list manual verification performed. Include screenshots for visible UI changes and note any new or updated image assets.
