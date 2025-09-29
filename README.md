# pdf2anki

Prototype web app that turns course PDFs into review-ready Anki decks.

The backend now defaults to an LLM-first extraction flow: uploaded PDFs are
segmented, chunked to fit the model context window, and each chunk is analysed by
an OpenAI model to produce grounded flashcards. When no API key is configured,
the service automatically falls back to the heuristic extractors described
below.

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

The frontend is pinned to Vite 4 so it works with **Node.js 16.20+**.
Using a newer LTS (18/20) is still recommended, but no longer required to run
the development server. If you do switch Node versions with a tool such as
`nvm`, reinstall dependencies afterwards.

```bash
cd frontend
npm install
npm run dev
```

The development server proxies API calls to the FastAPI instance running on port 8000.

## Card extraction heuristics

The backend combines lightweight NLP heuristics to produce higher quality cards:

* **Definitions** — detects "is/are", "est/sont", and colon-based statements in English and French.
* **Enumerations** — understands bullet lists, numbered steps, and sentences such as "X consists of …" to build Q/A and cloze cards.
* **Section summaries** — reuses detected headings to create concise recap questions for longer paragraphs.
* **Language-aware prompts** — question templates automatically switch between English and French based on the `language` field provided in the `/extract` request.

You can tweak the generation by changing the `language`, `card_types`, or `max_cards` parameters sent from the frontend.

### LLM-backed extraction

Provide an OpenAI API key to let the backend generate cards directly from PDF
chunks. The service keeps each prompt under a configurable token budget and
streams the chunks sequentially so even long documents stay within model limits.

```bash
export OPENAI_API_KEY=sk-your-key
# Optional overrides
export OPENAI_EXTRACTION_MODEL=gpt-4o-mini     # default model for extraction
export LLM_MAX_CHUNK_TOKENS=3200               # rough cap per prompt
export LLM_CHUNK_OVERLAP_TOKENS=200            # overlap between chunks
```

The `/extract` endpoint returns an `llm` report detailing how many cards the
model generated, how many chunks were needed, which model served the request, and
any failure messages. When the key is missing or a call fails, the backend
gracefully switches to the heuristic extractors so users still receive candidate
cards.

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
