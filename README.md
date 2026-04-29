# 📅 SlotAPI — Système de Réservation de Créneaux

SlotAPI est une solution backend robuste conçue pour gérer des ressources (professionnels, salles, équipements), définir leurs disponibilités et permettre la prise de rendez-vous avec un système de notifications automatisées (webhooks).

## 🚀 Fonctionnalités Clés

- **Gestion de Ressources** : Création et organisation des entités réservables.
- **Disponibilités Flexibles** : Définition de créneaux temporels précis avec détection de chevauchements.
- **Système de Réservation** : Processus de réservation complet avec statut de confirmation.
- **Notifications Automatisées** : Rappels planifiés à 24h et 1h avant le rendez-vous via `ARQ` (Redis).
- **Liste d'Attente** : Inscription automatique pour être notifié dès qu'un créneau se libère.
- **Sécurité** : Protection des endpoints administratifs via clé API (`X-API-Key`).

---

## 🛠️ Stack Technique

- **Framework** : FastAPI (Asynchrone)
- **Base de données** : PostgreSQL
- **ORM** : SQLAlchemy + Alembic (Migrations)
- **File d'attente** : Redis + ARQ
- **Conteneurisation** : Docker & Docker Compose
- **Tests** : Pytest

---

## 📦 Installation et Lancement

### 1. Configuration de l'environnement
Copiez le fichier d'exemple et configurez vos variables :
```bash
cp .env.example .env
```
*Note : La clé API par défaut pour le développement est `dev-secret-key`.*

### 2. Lancement avec Docker (Recommandé)
Lance l'API, la DB, Redis et le Worker en une commande :
```bash
docker compose up --build
```
- **API** : http://localhost:8000
- **Swagger UI** : http://localhost:8000/docs

### 3. Développement Local (Hors Docker)
```bash
# Installation des dépendances
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Appliquer les migrations
alembic upgrade head

# Lancer l'API (port 8000)
uvicorn app.main:app --reload

# Lancer le Worker (gestion des rappels)
arq app.workers.tasks.WorkerSettings
```

---

## 🔑 Authentification

Tous les endpoints (sauf les webhooks et la documentation) requièrent le header suivant :
`X-API-Key: dev-secret-key`

---

## 📖 Documentation des Endpoints

### 🏗️ Ressources
Gestion des entités pour lesquelles on peut réserver.

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/resources/` | Créer une nouvelle ressource. |
| `GET` | `/resources/` | Lister les ressources (Pagination: `skip`, `limit`). |
| `DELETE` | `/resources/{id}` | Supprimer une ressource et ses données liées. |

**Exemple Création :**
```bash
curl -X POST http://localhost:8000/resources/ \
     -H "Content-Type: application/json" \
     -H "X-API-Key: dev-secret-key" \
     -d '{"name": "Dr. Kofi", "type": "médecin"}'
```

---

### 📅 Disponibilités (Slots)
Définition du temps disponible pour une ressource.

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/resources/{res_id}/availability/` | Ajouter un ou plusieurs créneaux. |
| `GET` | `/resources/{res_id}/availability` | Voir les créneaux libres futurs. |

**Exemple Ajout de Slots :**
```bash
curl -X POST http://localhost:8000/resources/{res_id}/availability/ \
     -H "Content-Type: application/json" \
     -H "X-API-Key: dev-secret-key" \
     -d '{
       "slots": [
         {"start_time": "2026-10-01T10:00:00Z", "end_time": "2026-10-01T11:00:00Z"}
       ]
     }'
```

---

### 📝 Réservations
Gestion des rendez-vous.

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/bookings/` | Créer une réservation (planifie auto les rappels). |
| `GET` | `/bookings/` | Lister les réservations avec filtres (status, date, client). |
| `GET` | `/bookings/{id}` | Détails d'une réservation. |
| `DELETE` | `/bookings/{id}` | Annuler une réservation (impossible < 1h avant). |

**Exemple Réservation :**
```bash
curl -X POST http://localhost:8000/bookings/ \
     -H "Content-Type: application/json" \
     -H "X-API-Key: dev-secret-key" \
     -d '{
       "resource_id": "UUID-RESSOURCE",
       "slot_id": "UUID-SLOT",
       "client_name": "Jean Dupont",
       "client_phone": "+22890000000"
     }'
```

---

### ⏳ Liste d'attente (Bonus)
Permet aux clients d'être notifiés si un créneau déjà complet se libère.

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/slots/{slot_id}/waitlist/` | S'inscrire pour un créneau complet. |
| `GET` | `/slots/{slot_id}/waitlist/` | Voir la liste d'attente d'un créneau. |

**Exemple Inscription :**
```bash
curl -X POST http://localhost:8000/slots/{slot_id}/waitlist/ \
     -H "Content-Type: application/json" \
     -H "X-API-Key: dev-secret-key" \
     -d '{"client_name": "Alice", "client_phone": "+22891234567"}'
```

---

### 🔔 Notifications & Webhooks

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/bookings/{id}/notifications/` | Historique des rappels pour une réservation. |
| `POST` | `/webhooks/notify` | Endpoint de réception des notifications (Simulé). |

*Note : L'endpoint `/webhooks/notify` est public pour permettre la réception de requêtes externes ou internes.*

---

## 📮 Guide de Test avec Postman

1. **Importation** :
   - Allez dans Postman > **Import**.
   - Entrez l'URL : `http://localhost:8000/openapi.json` (quand le serveur tourne).
   - Postman générera automatiquement une collection avec tous les endpoints.

2. **Configuration de l'Auth** :
   - Dans votre collection, allez dans l'onglet **Headers**.
   - Ajoutez la clé `X-API-Key`.
   - Valeur : `dev-secret-key`.

3. **Exemple de Workflow de Test** :
   1. `POST /resources/` : Créez un médecin. Copiez l'ID.
   2. `POST /resources/{id}/availability/` : Ajoutez un créneau pour demain. Copiez l'ID du slot.
   3. `POST /bookings/` : Réservez ce créneau.
   4. `GET /bookings/{id}/notifications/` : Vérifiez que les notifications "24h_before" et "1h_before" sont créées avec le statut `PENDING`.

---

## 🧪 Exécution des Tests

Le projet utilise une base de données de test dédiée.
```bash
pytest -v
```
Les tests couvrent :
- La création et pagination des ressources.
- La détection des chevauchements de créneaux.
- Les contraintes d'annulation (limite de 1h).
- Le cycle de vie complet de la liste d'attente.
- La sécurité des clés API.

---

## 📁 Structure du Projet

```text
slot-api/
├── alembic/              # Scripts de migration DB
├── app/
│   ├── api/              # Routers FastAPI (Contrôleurs)
│   ├── models/           # Modèles SQLAlchemy (Database)
│   ├── schemas/          # Modèles Pydantic (Validation/Sérialisation)
│   ├── services/         # Logique métier (Calculs, DB ops)
│   ├── workers/          # Tâches de fond (Rappels via ARQ)
│   ├── main.py           # Point d'entrée de l'application
│   └── database.py       # Configuration SQLAlchemy
├── tests/                # Tests d'intégration et unitaires
├── docker-compose.yml    # Orchestration des conteneurs
└── Dockerfile            # Image Docker de l'API
```

---

## 🛡️ Gestion des Erreurs

- `400 Bad Request` : Données invalides, créneau dans le passé ou annulation trop tardive.
- `403 Forbidden` : Clé API manquante ou incorrecte.
- `404 Not Found` : Ressource, slot ou réservation inexistant.
- `409 Conflict` : Créneau déjà réservé ou chevauchement de disponibilité.