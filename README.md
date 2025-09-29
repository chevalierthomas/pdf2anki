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
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The development server proxies API calls to the FastAPI instance running on port 8000.
