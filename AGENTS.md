# Repository Guidelines

## Project Structure & Module Organization
The project follows an MVC layout centered on `main.py`. Domain models and database access live in `model/` and `database/`, while UI components live in `view/` and flow control resides in `controller/`. Shared utilities sit under `utils/`, configuration and environment templates in `config/`, and static assets in `assets/`. Tests are colocated in `tests/` with fixtures beside the code they cover, and scaffolding scripts (e.g., `create_migration.sh`) live at the repo root for quick access.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a local virtual environment.
- `pip install -r requirements.txt`: install runtime dependencies.
- `python main.py --migrate`: apply pending database migrations before running the GUI.
- `python main.py`: launch the PyQt5 desktop application in the current environment.
- `python -m pytest`: run the full test suite; add `-k name` to scope to a module during iteration.
- `bash build_release.sh`: build the distributable bundle used for shipping releases.

## Coding Style & Naming Conventions
Write Python with four-space indentation and PEP 8 semantics, keeping lines ≤100 characters. Modules should be snake_case (`font_manager.py`), classes in PascalCase, and user-facing strings centralized in the relevant view/controller. Static analysis is enforced with `flake8`, imports must remain sorted via `isort --profile black`, and type hints are required because `mypy` is configured to reject untyped definitions.

## Testing Guidelines
Pytest discovers files named `test_*.py`, classes prefixed with `Test`, and functions named `test_*`. Maintain descriptive test names that mirror the feature under test (e.g., `test_font_dialog_persists_user_choice`). The default invocation enforces ≥80% coverage and emits an HTML report in `htmlcov/`; review regressions locally before opening a pull request.

## Commit & Pull Request Guidelines
Write commits with a succinct, present-tense subject (`Add ship manifest export`) and include context in the body when the change is non-trivial. Reference issues with `#ID` when applicable. Pull requests should summarize intent, list validation steps (tests, manual flows), attach screenshots for UI updates, and call out database or migration impacts so reviewers know how to reproduce your setup.

## Configuration & Data Safety
Duplicate `config/.env.example` to `config/.env`, fill in credentials, and never commit secrets. The sample `secret.py` is a stub; store real keys via environment variables instead. Sanitise exported data before sharing logs or fixtures, and rotate API keys when working with third-party font providers.
