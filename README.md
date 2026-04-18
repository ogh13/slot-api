# 📅 SlotAPI — Test Technique Stagiaire Backend

> **Poste visé :** Stagiaire Développeur Backend  
> **Stack attendue :** FastAPI · PostgreSQL · Redis · Docker  
> **Soumission :** Fork ce repo → développe → envoie le lien de ton repo à [recrutement@karaba.africa]

---

## Contexte

Karaba automatise des processus métier via des bots conversationnels WhatsApp. L'un des besoins fondamentaux de cette infrastructure est un **moteur de réservation de créneaux** — capable de gérer des ressources (agents, professionnels, salles), leurs disponibilités, et d'envoyer des rappels automatiques aux parties concernées.

Ton mission : construire **SlotAPI**, une API REST robuste de gestion de réservations avec notifications différées.

---

## Ce que tu vas construire

### 1. Gestion des ressources

```
POST   /resources          → créer une ressource (ex: "Dr. Kofi", "Agent RH")
GET    /resources          → lister toutes les ressources
DELETE /resources/{id}     → supprimer une ressource
```

Une ressource a : `id`, `name`, `type` (libre : médecin, agent, salle…), `created_at`

---

### 2. Gestion des disponibilités

```
POST   /resources/{id}/availability   → définir des créneaux disponibles
GET    /resources/{id}/availability   → voir les créneaux disponibles (non réservés)
```

Un créneau a : `start_time`, `end_time`, `is_booked` (bool)

**Règles métier obligatoires :**
- Deux créneaux d'une même ressource ne peuvent pas se chevaucher
- Un créneau dans le passé ne peut pas être créé

---

### 3. Réservations

```
POST   /bookings           → créer une réservation
GET    /bookings/{id}      → détail d'une réservation
DELETE /bookings/{id}      → annuler une réservation
GET    /bookings           → lister (avec filtres : resource_id, date, status)
```

Une réservation a : `id`, `resource_id`, `slot_id`, `client_name`, `client_phone`, `status` (`confirmed` / `cancelled`), `created_at`

**Règles métier obligatoires :**
- On ne peut pas réserver un créneau déjà réservé
- L'annulation est impossible moins de 1h avant le créneau (retourner une erreur métier claire)

---

### 4. Notifications différées (Redis + Celery ou ARQ)

Lors de la création d'une réservation, planifier automatiquement :

- Un rappel **24h avant** le créneau
- Un rappel **1h avant** le créneau

Ces rappels ne font pas vraiment d'envoi — ils appellent un **webhook interne** simulé :

```
POST /webhooks/notify
{
  "booking_id": "...",
  "client_phone": "+228XXXXXXXX",
  "message": "Rappel : votre rendez-vous est dans 1h avec Dr. Kofi",
  "trigger": "1h_before"
}
```

Cet endpoint doit logger la notification reçue et retourner `200 OK`. C'est suffisant.

---

### 5. Statut des notifications

```
GET /bookings/{id}/notifications   → liste les notifications planifiées et leur statut (pending / sent)
```

---

## Fonctionnalités bonus _(non obligatoires, mais appréciées)_

- [ ] Auth simple par API Key (header `X-API-Key`) pour protéger les endpoints d'admin
- [ ] Liste d'attente : si un créneau est complet, possibilité de s'inscrire et être notifié si une annulation survient
- [ ] Pagination sur les endpoints de liste
- [ ] Tests unitaires et d'intégration (pytest)
- [ ] CI GitHub Actions (lint + tests)

---

## Ce qu'on évalue

| Critère | Points |
|---|---|
| Fonctionnalités obligatoires livrées | 30 |
| Qualité du code Python (structure, lisibilité) | 20 |
| Modélisation PostgreSQL (migrations Alembic) | 15 |
| Docker Compose qui fonctionne du premier coup | 15 |
| Gestion des erreurs (codes HTTP, messages clairs) | 10 |
| Bonus | +10 |

---

## Contraintes techniques

- **FastAPI** uniquement (pas Flask, pas Django)
- **PostgreSQL** pour la persistance — SQLAlchemy + Alembic pour les migrations
- **Redis** pour la queue de tâches
- **Docker Compose** obligatoire : `docker compose up` doit lancer l'ensemble (API + DB + Redis + Worker)
- Python 3.11+
- Pas de frontend requis

---

## Structure de repo attendue

```
slotapi/
├── app/
│   ├── api/
│   │   ├── resources.py
│   │   ├── bookings.py
│   │   └── webhooks.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── workers/
│   └── main.py
├── alembic/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Comment soumettre

1. **Fork** ce repository
2. Développe sur ta propre branche ou directement sur `main`
3. Assure-toi que `docker compose up` démarre tout sans erreur
4. Inclus dans ton README : les endpoints disponibles + comment tester avec curl ou Postman
5. Envoie le lien de ton repo GitHub à **recrutement@karaba.africa** avec en objet : `[STAGE BACKEND] Ton Nom`

> ⚠️ Un repo sans Docker Compose fonctionnel ou sans documentation des endpoints sera automatiquement écarté.

---

## Questions ?

Ouvre une **GitHub Issue** sur ce repo. On répond sous 48h.
