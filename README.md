# Quiz App

A desktop quiz application for preparing for:

- Google Cloud Professional Cloud Architect (`PCA`)
- Google Cloud Professional Cloud Security Engineer (`PCS`)
- HashiCorp Terraform Associate (`TFA`)

Built with Python, Tkinter, Pillow, and `ttkbootstrap`.

## Features

- Single-choice and multiple-choice questions with automatic grading
- Separate selectable question banks for each exam
- Optional question and answer shuffling
- Image-based questions with click-to-enlarge support
- Explanations, score tracking, and incorrect-answer review
- Sample Test mode with 50 randomly selected questions
- Automatic saving of the selected exam, question bank, and shuffle settings

## Requirements

- Python 3.10 or newer
- Tkinter support

Tkinter is normally included with Python on Windows and macOS. On Debian or
Ubuntu, install it with:

```bash
sudo apt install python3-tk
```

## Installation

```bash
git clone <repository-url>
cd quiz-app
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

## Running the App

```bash
python3 main.py
```

Use **Options** to select an exam, load a question bank, enable shuffling, or
start Sample Test mode.

### Keyboard Shortcuts

| Key | Action |
| --- | --- |
| `A`-`Z` | Select the matching answer option |
| `Enter` | Submit the current answer |
| `Ctrl+D` | Show the question description |
| `Ctrl+G` | Go to a question |
| `Ctrl+S` | Show results |

## Question Banks

Question files are stored as `questions/<EXAM>/quiz_data_<number>.json`. Each
question uses this structure:

```json
{
  "id": 1,
  "question": "Question text",
  "choices": ["A. First option", "B. Second option"],
  "answer": "A",
  "image": null,
  "description": "Optional explanation"
}
```

For multiple-choice questions, use an answer list such as `["A", "C"]`.
Relative image paths are resolved from the question bank's directory.

Validate edited JSON before launching the app:

```bash
python3 -m json.tool questions/PCA/quiz_data_1.json >/dev/null
```
