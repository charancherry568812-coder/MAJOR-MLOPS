"""Bank Management API Test Suite."""

def test_list_banks(client, auth_headers):
    res = client.get("/api/v1/banks", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 4
    codes = [b["code"] for b in data["items"]]
    assert "BANK-001" in codes
    assert "BANK-002" in codes
    assert "BANK-003" in codes
    assert "BANK-004" in codes


def test_get_bank_detail(client, auth_headers):
    list_res = client.get("/api/v1/banks", headers=auth_headers)
    bank_id = list_res.json()["data"]["items"][0]["id"]

    res = client.get(f"/api/v1/banks/{bank_id}", headers=auth_headers)
    assert res.status_code == 200
    bank = res.json()["data"]
    assert bank["id"] == bank_id
    assert "code" in bank
    assert "name" in bank


import uuid


def test_create_bank(client, auth_headers):
    unique_code = f"BNK-{uuid.uuid4().hex[:5].upper()}"
    payload = {
        "name": f"Omega Mutual Bank {unique_code}",
        "code": unique_code,
        "branch": "Pacific Headquarters",
        "contact_person": "Olivia Thorne",
        "email": f"{unique_code.lower()}@omegabank.com",
        "phone": "+1-555-0999",
        "location": "Seattle, WA",
    }
    res = client.post("/api/v1/banks", json=payload, headers=auth_headers)
    assert res.status_code in (201, 200)
    data = res.json()["data"]
    assert data["code"] == unique_code
