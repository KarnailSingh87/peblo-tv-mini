import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.main import app
from backend.app.db.session import get_db
from backend.app.models.entities import Base, User
from backend.app.core.security import get_password_hash

# Uses shared fixtures from conftest.py

def test_valid_login(client):
    # Test editor login
    resp = client.post("/api/v1/auth/login", json={"username": "editor", "password": "editor123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "editor"
    assert data["user"]["role"] == "editor"

    # Test admin login
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"

def test_invalid_login(client):
    # Wrong password
    resp = client.post("/api/v1/auth/login", json={"username": "editor", "password": "wrongpassword"})
    assert resp.status_code == 401
    assert "Incorrect username or password" in resp.json()["detail"]

    # Non-existent user
    resp = client.post("/api/v1/auth/login", json={"username": "nonexistent", "password": "password123"})
    assert resp.status_code == 401

def test_editor_permissions(client):
    # Obtain editor token
    login_resp = client.post("/api/v1/auth/login", json={"username": "editor", "password": "editor123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Editor can view me
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "editor"

    # 2. Editor can access show creation
    show_resp = client.post("/api/v1/shows", json={"title": "Test Show", "slug": "test-show", "status": "draft"}, headers=headers)
    assert show_resp.status_code == 201

    # 3. Editor can access episode creation
    season_id = show_resp.json()["seasons"][1]["id"]
    ep_resp = client.post(f"/api/v1/seasons/{season_id}/episodes", json={"episode_title": "Test Ep", "content_group": "cg-1", "language": "en"}, headers=headers)
    assert ep_resp.status_code == 201

    # 4. Editor can access artwork upload
    from backend.tests.test_artwork import _create_test_image
    banner_bytes = _create_test_image(1280, 720, format="JPEG")
    files = {"file": ("banner.jpg", banner_bytes, "image/jpeg")}
    data = {"artwork_type": "banner", "entity_type": "show", "entity_id": show_resp.json()["id"]}
    art_resp = client.post("/api/v1/artwork/upload", data=data, files=files, headers=headers)
    assert art_resp.status_code == 201

    # 5. Editor can access validation report
    val_resp = client.get("/api/v1/admin/validation-report", headers=headers)
    assert val_resp.status_code == 200

def test_editor_denied_from_publishing(client):
    # Obtain editor token
    login_resp = client.post("/api/v1/auth/login", json={"username": "editor", "password": "editor123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Editor MUST receive HTTP 403 Forbidden on publish
    pub_resp = client.post("/api/v1/admin/catalog/publish", headers=headers)
    assert pub_resp.status_code == 403
    assert "Forbidden" in pub_resp.json()["detail"]

    # Editor MUST receive HTTP 403 Forbidden on publish history
    hist_resp = client.get("/api/v1/admin/catalog/publish-runs", headers=headers)
    assert hist_resp.status_code == 403

def test_admin_access(client):
    # Obtain admin token
    login_resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Admin can perform editor actions
    assert client.post("/api/v1/shows", json={"title": "Admin Show", "slug": "admin-show", "status": "draft"}, headers=headers).status_code == 201
    assert client.get("/api/v1/admin/validation-report", headers=headers).status_code == 200

    # Admin CAN access publishing endpoint (HTTP 200)
    pub_resp = client.post("/api/v1/admin/catalog/publish", headers=headers)
    assert pub_resp.status_code == 200
    assert pub_resp.json()["status"] == "success"

    # Admin CAN access publish history
    hist_resp = client.get("/api/v1/admin/catalog/publish-runs", headers=headers)
    assert hist_resp.status_code == 200
