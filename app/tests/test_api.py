import os
os.environ["DB_PATH"] = "/tmp/teste_tarefas.db"

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_criar_e_listar():
    r = client.post("/api/tarefas", json={"titulo": "estudar nuvem"})
    assert r.status_code == 201
    titulos = [t["titulo"] for t in client.get("/api/tarefas").json()]
    assert "estudar nuvem" in titulos


def test_titulo_vazio():
    assert client.post("/api/tarefas", json={"titulo": "  "}).status_code == 400


def test_concluir_inexistente():
    assert client.put("/api/tarefas/99999/concluir").status_code == 404


def test_metricas():
    assert "http_requests_total" in client.get("/metrics").text
