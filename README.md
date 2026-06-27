# GitHub Companion
GitHub Companion is a personal command-line tool that eliminates unnecessary visits to GitHub by providing essential Git and GitHub information directly in the terminal.


## Target Audience

Developers who frequently switch between their editor and GitHub just to check simple information like contribution streaks, commit status, or repository activity.



## Core Commands:

- heatmap
- pushed
- latest
- status
- profile

These are the core commands planned for Version 1. Additional commands and features will be introduced in future releases.

## Goals

- Reduce unnecessary GitHub visits.
- Reduce context switching.
- Keep developers inside the terminal.
- Provide fast access to Git and GitHub information.


## Project structure

- `app.py` - application entry point
- `commands/` - command modules for dashboard, status, heatmap, streak, focus, doctor, and shutdown
- `services/` - service layers for GitHub integration, Git access, and analytics
- `utils/` - configuration and helper utilities
- `models/` - data models and domain classes
- `config/` - configuration files and templates
- `tests/` - unit tests


## Project Status

🚧 Under Development

GitHub Companion is currently in active development.
Version 1 focuses on solving the most common GitHub workflow interruptions.


## Getting started

1. Create a virtual environment:

```bash
python -m venv .venv
```

2. Activate it:

- Windows (PowerShell): `.
venv\Scripts\Activate.ps1`
- Windows (cmd): `.\venv\Scripts\activate.bat`

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the app:

```bash
python app.py
```
