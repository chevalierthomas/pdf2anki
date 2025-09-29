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

### Optional LLM polishing

If you want richer phrasing, short rationales, or better tag suggestions, provide
an OpenAI API key and enable the *Enhance with AI* toggle in the frontend. The
backend will pass the generated cards through `gpt-4o-mini` (or the model you
configure) to rewrite the question/answer pair while staying faithful to the
original PDF snippet.

```bash
export OPENAI_API_KEY=sk-your-key
# Optional: override defaults
export OPENAI_MODEL=gpt-4o-mini    # any Responses/Chat model works
export LLM_REFINEMENT_LIMIT=20     # max cards polished per request
```

With a key in place, the `/extract` response contains an `llm` report detailing
whether refinement happened, how many cards were enriched, and how long it took.
If no key is configured, the API responds with `used: false` and the frontend
explains that AI polishing was skipped.

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
