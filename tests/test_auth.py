"""Authentication & RBAC Test Suite."""

def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={"email": "admin@fedbank.com", "password": "Admin@123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "admin@fedbank.com"
    assert data["user"]["role"]["name"] == "SUPER_ADMIN"


def test_login_all_demo_roles(client):
    demo_accounts = [
        ("banka.admin@fedbank.com", "BankA@123", "BANK_ADMIN"),
        ("bankb.admin@fedbank.com", "BankB@123", "BANK_ADMIN"),
        ("data.scientist@fedbank.com", "DataSci@123", "DATA_SCIENTIST"),
        ("ml.engineer@fedbank.com", "MLEng@123", "ML_ENGINEER"),
        ("auditor@fedbank.com", "Auditor@123", "AUDITOR"),
        ("viewer@fedbank.com", "Viewer@123", "VIEWER"),
    ]
    for email, pwd, expected_role in demo_accounts:
        res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        assert res.status_code == 200, f"Failed for {email}: {res.text}"
        data = res.json()
        assert data["user"]["role"]["name"] == expected_role


def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={"email": "admin@fedbank.com", "password": "WrongPassword!"})
    assert res.status_code == 401


def test_token_refresh(client):
    res = client.post("/api/v1/auth/login", json={"email": "admin@fedbank.com", "password": "Admin@123"})
    refresh_token = res.json()["refresh_token"]

    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    assert "access_token" in ref_res.json()
