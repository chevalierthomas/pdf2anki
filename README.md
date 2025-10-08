# PDF2Anki

Application web complète pour transformer rapidement un fichier PDF en deck Anki prêt à l'emploi.

## Structure du projet

- `backend/` — API FastAPI. Elle reçoit un fichier PDF, extrait le texte, génère des cartes et construit un fichier `.apkg` à télécharger.
- `frontend/` — Interface Vue 3 avec Vite offrant une expérience moderne de dépôt de fichier.

## Démarrage rapide

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

L'interface de développement du frontend proxy automatiquement les requêtes `/api` vers `http://localhost:8000`.

## Tests

```bash
cd backend
pytest
```

## Génération d'un deck

1. Ouvrez l'interface web.
2. Glissez-déposez ou sélectionnez votre PDF.
3. Cliquez sur « Générer le deck ».
4. Téléchargez le fichier `.apkg` proposé et importez-le dans Anki.

Les cartes sont générées via une heuristique simple qui détecte les structures « terme : définition » et scinde les paragraphes en question/réponse.
