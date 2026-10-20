import os
import subprocess
import sys
import tempfile
from pathlib import Path

_db = tempfile.TemporaryDirectory()
os.environ.update(KANDANGULAR_ENV="development", KANDANGULAR_SECRET_KEY="s" * 64, KANDANGULAR_API_TOKEN="t" * 64, KANDANGULAR_DB_PATH=str(Path(_db.name) / "test.sqlite3"), KANDANGULAR_ALLOWED_HOSTS="testserver,localhost")
from kandangular.asgi import application
from django.core.management import call_command
from starlette.testclient import TestClient

call_command("migrate", verbosity=0)
client = TestClient(application)
auth = {"Authorization": "Bearer " + "t" * 64}

def test_surfaces_and_headers():
    for path in ["/", "/healthz", "/plugins/status", "/admin/login/"]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
    assert "KandangUlar" in client.get("/").text

def test_auth_validation_and_persistence():
    assert client.get("/api/v1/projects").status_code == 401
    assert client.post("/api/v1/projects", json={"name": "a"}).status_code == 401
    assert client.get("/api/v1/projects", headers={"Authorization": "Bearer wrong"}).status_code == 401
    for payload in [{"name": " "}, {"name": "x" * 121}, {"name": "ok", "unknown": True}]:
        assert client.post("/api/v1/projects", json=payload, headers=auth).status_code == 422
    response = client.post("/api/v1/projects", json={"name": "Proyek ular"}, headers=auth)
    assert response.status_code == 201
    assert any(p["id"] == response.json()["id"] for p in client.get("/api/v1/projects", headers=auth).json())
    assert client.get("/api/v1/projects?limit=101", headers=auth).status_code == 422

def test_host_and_csrf():
    assert client.get("/healthz", headers={"Host": "evil.example"}).status_code == 400
    assert client.post("/admin/login/", data={"username": "admin", "password": "bad"}).status_code == 403

def production(env_extra, script):
    env = {**os.environ, "KANDANGULAR_ENV": "production", "KANDANGULAR_ALLOWED_HOSTS": "testserver", **env_extra}
    return subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True)

def test_production_rejects_missing_secret_and_wildcard():
    for overrides in [{"KANDANGULAR_SECRET_KEY": ""}, {"KANDANGULAR_ALLOWED_HOSTS": "*"}, {"KANDANGULAR_API_TOKEN": ""}]:
        assert production(overrides, "import kandangular.asgi").returncode != 0

def test_production_https_and_docs():
    result = production({}, '''from kandangular.asgi import application
from starlette.testclient import TestClient
c = TestClient(application, base_url="https://testserver")
assert c.get("/api/docs").status_code == 404
assert c.get("/healthz").headers["strict-transport-security"]
assert c.get("http://testserver/healthz", follow_redirects=False).status_code == 307
''')
    assert result.returncode == 0, result.stderr
