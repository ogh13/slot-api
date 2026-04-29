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

## 🧪 Exemples de requêtes (curl)

Voici quelques exemples pour tester l'API. N'oubliez pas de remplacer `<VOTRE_CLE_API>` par la valeur définie dans votre fichier `.env`.

### 1. Créer une ressource
```bash
curl -X POST http://localhost:8000/resources/ \
     -H "Content-Type: application/json" \
     -H "X-API-Key: <VOTRE_CLE_API>" \
     -d '{"name": "Dr. Kofi", "type": "médecin"}'
```

### 2. Ajouter des disponibilités pour une ressource
```bash
# Remplacez {resource_id} par l'ID retourné lors de la création
curl -X POST http://localhost:8000/resources/{resource_id}/availability/ \
     -H "Content-Type: application/json" \
     -H "X-API-Key: <VOTRE_CLE_API>" \
     -d '{
       "slots": [
         {
           "start_time": "2026-05-01T10:00:00Z",
           "end_time": "2026-05-01T11:00:00Z"
         }
       ]
     }'
```

### 3. Créer une réservation
```bash
curl -X POST http://localhost:8000/bookings/ \
     -H "Content-Type: application/json" \
     -H "X-API-Key: <VOTRE_CLE_API>" \
     -d '{
       "resource_id": "{resource_id}",
       "slot_id": "{slot_id}",
       "client_name": "Jean Dupont",
       "client_phone": "+22890000000"
     }'
```

## 📮 Utilisation avec Postman / Insomnia

1. **Importation** : Vous pouvez importer la documentation Swagger directement via `http://localhost:8000/openapi.json`.
2. **Authentification** : Dans l'onglet **Headers**, ajoutez la clé `X-API-Key` avec votre token secret.
3. **Corps des requêtes** : Pour les `POST`, utilisez le format **Body** > **raw** > **JSON**.
