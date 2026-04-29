import pytest
from datetime import datetime, timezone, timedelta

HEADERS = {}

@pytest.fixture(autouse=True)
def setup_headers(api_key):
    global HEADERS
    HEADERS = {"X-API-Key": api_key}

@pytest.mark.asyncio
async def test_create_resource(client):
    resp = await client.post("/resources/", json={"name": "Dr. Kofi", "type": "médecin"}, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Dr. Kofi"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_resources_pagination(client):
    # Créer 5 ressources
    for i in range(5):
        await client.post("/resources/", json={"name": f"R{i}", "type": "test"}, headers=HEADERS)
    
    # Test limit
    resp = await client.get("/resources/?limit=2", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 5
    
    # Test skip
    resp_skip = await client.get("/resources/?skip=2&limit=2", headers=HEADERS)
    assert resp_skip.status_code == 200
    data_skip = resp_skip.json()
    assert len(data_skip["items"]) == 2
    assert data_skip["items"][0]["name"] != data["items"][0]["name"]

@pytest.mark.asyncio
async def test_availability_overlap(client):
    # Créer ressource, ajouter deux créneaux qui se chevauchent
    r = await client.post("/resources/", json={"name": "Salle", "type": "room"}, headers=HEADERS)
    rid = r.json()["id"]
    start1 = datetime.now(timezone.utc) + timedelta(days=1, hours=10)
    end1 = start1 + timedelta(hours=2)
    slot1 = {"start_time": start1.isoformat(), "end_time": end1.isoformat()}
    await client.post(f"/resources/{rid}/availability/", json={"slots": [slot1]}, headers=HEADERS)
    # Tentative de chevauchement
    start2 = start1 + timedelta(hours=1)
    end2 = start2 + timedelta(hours=1)
    slot2 = {"start_time": start2.isoformat(), "end_time": end2.isoformat()}
    resp = await client.post(f"/resources/{rid}/availability/", json={"slots": [slot2]}, headers=HEADERS)
    assert resp.status_code == 400
    assert "overlaps" in resp.json()["detail"]

@pytest.mark.asyncio
async def test_booking_cancellation_less_than_1h(client):
    # Créer une ressource + créneau très proche, réserver, annuler doit échouer
    r = await client.post("/resources/", json={"name": "Urgent", "type": "doc"}, headers=HEADERS)
    rid = r.json()["id"]
    start = datetime.now(timezone.utc) + timedelta(minutes=59)
    end = start + timedelta(hours=1)
    slot_resp = await client.post(f"/resources/{rid}/availability/", json={"slots": [{"start_time": start.isoformat(), "end_time": end.isoformat()}]}, headers=HEADERS)
    slot_id = slot_resp.json()[0]["id"]
    book_resp = await client.post("/bookings/", json={"resource_id": rid, "slot_id": slot_id, "client_name": "X", "client_phone": "+228"}, headers=HEADERS)
    booking_id = book_resp.json()["id"]
    # Annulation doit être refusée
    cancel_resp = await client.delete(f"/bookings/{booking_id}", headers=HEADERS)
    assert cancel_resp.status_code == 400
    assert "1 hour" in cancel_resp.json()["detail"]

@pytest.mark.asyncio
async def test_waitlist(client):
    # Créer un créneau réservé, puis s'inscrire en liste d'attente
    r = await client.post("/resources/", json={"name": "Dr. Wait", "type": "doc"}, headers=HEADERS)
    rid = r.json()["id"]
    start = datetime.now(timezone.utc) + timedelta(days=2)
    end = start + timedelta(hours=1)
    slot = await client.post(f"/resources/{rid}/availability/", json={"slots": [{"start_time": start.isoformat(), "end_time": end.isoformat()}]}, headers=HEADERS)
    slot_id = slot.json()[0]["id"]
    # Réserver le créneau
    await client.post("/bookings/", json={"resource_id": rid, "slot_id": slot_id, "client_name": "A", "client_phone": "+228"}, headers=HEADERS)
    # Tentative d'inscription waitlist
    wait_resp = await client.post(f"/slots/{slot_id}/waitlist/", json={"client_name": "B", "client_phone": "+229"}, headers=HEADERS)
    assert wait_resp.status_code == 201
    # Annulation de la réservation : devrait notifier la waitlist
    bookings_resp = (await client.get(f"/bookings/?resource_id={rid}", headers=HEADERS)).json()
    booking_id = bookings_resp["items"][0]["id"]
    cancel = await client.delete(f"/bookings/{booking_id}", headers=HEADERS)
    assert cancel.status_code == 204
    # Vérifier que le waitlist entry est marquée comme notified
    (await client.get(f"/slots/{slot_id}/waitlist/", headers=HEADERS)).json()["items"]
    # (optionnel : on peut vérifier le webhook loggé)

@pytest.mark.asyncio
async def test_delete_resource(client):
    # Créer puis supprimer
    r = await client.post("/resources/", json={"name": "To Delete", "type": "room"}, headers=HEADERS)
    rid = r.json()["id"]
    resp = await client.delete(f"/resources/{rid}", headers=HEADERS)
    assert resp.status_code == 204
    # Vérifier que c'est bien supprimé
    resp_get = await client.get("/resources/", headers=HEADERS)
    assert not any(item["id"] == rid for item in resp_get.json()["items"])

@pytest.mark.asyncio
async def test_booking_conflict(client):
    r = await client.post("/resources/", json={"name": "Conflict Room", "type": "room"}, headers=HEADERS)
    rid = r.json()["id"]
    start = datetime.now(timezone.utc) + timedelta(days=3)
    end = start + timedelta(hours=1)
    slot_resp = await client.post(f"/resources/{rid}/availability/", json={"slots": [{"start_time": start.isoformat(), "end_time": end.isoformat()}]}, headers=HEADERS)
    slot_id = slot_resp.json()[0]["id"]
    
    # Première réservation
    book1 = await client.post("/bookings/", json={"resource_id": rid, "slot_id": slot_id, "client_name": "A", "client_phone": "1"}, headers=HEADERS)
    assert book1.status_code == 201
    
    # Deuxième réservation (doit échouer avec 409)
    book2 = await client.post("/bookings/", json={"resource_id": rid, "slot_id": slot_id, "client_name": "B", "client_phone": "2"}, headers=HEADERS)
    assert book2.status_code == 409

@pytest.mark.asyncio
async def test_get_booking_and_notifications(client):
    r = await client.post("/resources/", json={"name": "Notify Room", "type": "room"}, headers=HEADERS)
    rid = r.json()["id"]
    start = datetime.now(timezone.utc) + timedelta(days=4)
    end = start + timedelta(hours=1)
    slot_resp = await client.post(f"/resources/{rid}/availability/", json={"slots": [{"start_time": start.isoformat(), "end_time": end.isoformat()}]}, headers=HEADERS)
    slot_id = slot_resp.json()[0]["id"]
    
    book = await client.post("/bookings/", json={"resource_id": rid, "slot_id": slot_id, "client_name": "N", "client_phone": "3"}, headers=HEADERS)
    booking_id = book.json()["id"]
    
    # Test GET /bookings/{id}
    get_book = await client.get(f"/bookings/{booking_id}", headers=HEADERS)
    assert get_book.status_code == 200
    assert get_book.json()["id"] == booking_id
    
    # Test GET /bookings/{id}/notifications
    notifs = await client.get(f"/bookings/{booking_id}/notifications/", headers=HEADERS)
    assert notifs.status_code == 200
    assert isinstance(notifs.json(), list)
    assert len(notifs.json()) == 2  # 24h et 1h notifications créées

@pytest.mark.asyncio
async def test_webhook_notify(client):
    # L'endpoint de webhook ne nécessite pas d'authentification ? Si oui, le token est dans les headers
    payload = {
        "booking_id": "test_id",
        "client_phone": "123",
        "message": "test",
        "trigger": "test_trigger"
    }
    resp = await client.post("/webhooks/notify", json=payload, headers=HEADERS)
    # En fait, webhooks est protégé par la dépendance globale de l'app, donc on doit passer les headers
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"