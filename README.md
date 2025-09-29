# pdf2anki

Prototype web app that turns course PDFs into review-ready Anki decks.

## Project structure

```
pdf2anki/
├─ backend/         # FastAPI service for extraction + Anki export
└─ frontend/        # Vue 3 single-page app (Vite + Tailwind)
```

## Getting started

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn app:app --reload
```

> **Note:** Some Linux distributions do not ship a `python` shim by default.
> If `python` is not found, install the `python-is-python3` package or use
> `python3` in the commands above.

### Frontend

The Vite tooling requires **Node.js 18 or newer**. If your system Node is
older, switch versions with a tool like `nvm` before running the dev server.

```bash
cd frontend
npm install
npm run dev
```

The development server proxies API calls to the FastAPI instance running on port 8000.

## Pushing your changes

This template repository does not ship with a remote configured. To publish the
current branch to your own Git remote:

```bash
# inside the project root
git remote add origin <your-repo-url>
git push -u origin work
```

Replace `<your-repo-url>` with the HTTPS or SSH URL of a repository you own
(for example, one created on GitHub). Subsequent pushes can use `git push`
without additional arguments once the upstream has been set.
