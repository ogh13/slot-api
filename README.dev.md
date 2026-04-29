# 🛠️ Guide de Développement — SlotAPI

Ce guide explique comment configurer et lancer l'environnement de développement pour le projet SlotAPI.

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir installé :
- [Docker](https://www.docker.com/get-started) et Docker Compose.
- [Python 3.11+](https://www.python.org/downloads/) (pour le développement hors Docker).
- Un client API comme [Postman](https://www.postman.com/) ou [Insomnia](https://insomnia.rest/).

---

## 🚀 Lancement Rapide (Docker Compose)

C'est la méthode recommandée pour faire tourner l'ensemble de l'infrastructure (API, Worker, PostgreSQL, Redis).

1. **Cloner le dépôt**
2. **Créer un fichier `.env`** à la racine en vous basant sur le modèle de `.env.example` et des variables attendues dans `app/config.py`.
3. **Lancer les services :**
   ```bash
   docker compose up --build
   ```

L'API sera accessible sur `http://localhost:8000`.
La documentation Swagger sera disponible sur `http://localhost:8000/docs`.

---

## 💻 Développement Local (Hors Docker)

Si vous souhaitez modifier le code avec un rechargement automatique (hot-reload) plus performant :

### 1. Environnement Virtuel
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Services de support
Vous avez toujours besoin d'une base de données et de Redis. Vous pouvez les lancer via Docker :
```bash
docker run --name slot-db -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres
docker run --name slot-redis -p 6379:6379 -d redis
```

### 3. Migrations de base de données
Alembic est utilisé pour gérer le schéma de la base de données.
```bash
# Appliquer les migrations
alembic upgrade head

# Créer une nouvelle migration après modification d'un modèle
alembic revision --autogenerate -m "description du changement"
```

### 4. Lancer l'API
```bash
uvicorn app.main:app --reload
```

### 5. Lancer le Worker (ARQ)
Le worker gère les notifications différées.
```bash
arq app.workers.tasks.WorkerSettings
```

---

## 🧪 Tests

Les tests utilisent `pytest` et `httpx` pour les appels asynchrones.

```bash
# Lancer tous les tests
pytest

# Lancer avec les logs détaillés
pytest -v
```

---

## 🔑 Authentification

La plupart des endpoints (sauf les webhooks et la doc) sont protégés par une clé API.
Ajoutez le header suivant à vos requêtes :
`X-API-Key: <VOTRE_CLE_API>` (définie dans votre `.env`).

---

## 🛠️ Structure du code

- `app/api/` : Les routeurs FastAPI (points d'entrée).
- `app/models/` : Modèles SQLAlchemy (schéma DB).
- `app/schemas/` : Schémas Pydantic (validation des données).
- `app/services/` : Logique métier (manipulation de la DB, calculs).
- `app/workers/` : Définition des tâches de fond ARQ.

---

## 📝 Aide-mémoire Webhooks

Pour tester les notifications sans attendre 24h :
1. Créez un créneau proche (ex: dans 65 minutes).
2. Réservez-le.
3. Surveillez les logs du container `worker` ou de la console `arq`.
4. Vérifiez que l'endpoint `POST /webhooks/notify` reçoit bien le payload.

---

