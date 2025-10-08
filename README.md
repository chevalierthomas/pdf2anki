# PDF2Anki

Application web complète pour transformer rapidement un fichier PDF en deck Anki prêt à l'emploi.

> ℹ️ Depuis cette version, la génération de cartes tente d'utiliser l'API ChatGPT. Si aucune clé OpenAI n'est disponible, une heuristique locale de secours est appliquée.

## Structure du projet

- `backend/` — API FastAPI. Elle reçoit un fichier PDF, extrait le texte, génère des cartes, renvoie leur prévisualisation et construit un fichier `.apkg` encodé en Base64 pour téléchargement.
- `frontend/` — Interface Vue 3 avec Vite offrant une expérience moderne de dépôt de fichier.

## Démarrage rapide

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export OPENAI_API_KEY="votre_cle"
# optionnel : export OPENAI_MODEL="gpt-4o-mini"
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

L'interface de développement du frontend proxy automatiquement les requêtes `/api` vers `http://localhost:8000`.

> 💡 Les dépendances front-end ciblent désormais Vite 4, compatible avec Node.js 16+ pour éviter les erreurs `crypto.getRandomValues` observées avec Node 16.

## Tests

```bash
cd backend
pytest
```

## Génération d'un deck

1. Ouvrez l'interface web.
2. Glissez-déposez ou sélectionnez votre PDF.
3. Cliquez sur « Générer le deck ».
4. Passez en revue la prévisualisation des cartes proposées.
5. Téléchargez le fichier `.apkg` fourni et importez-le dans Anki.

Les cartes sont générées via l'API ChatGPT lorsqu'une clé `OPENAI_API_KEY` est configurée. En cas d'échec ou d'absence de clé, le système retombe sur une heuristique locale détectant les structures « terme : définition » et scindant les paragraphes en question/réponse.
