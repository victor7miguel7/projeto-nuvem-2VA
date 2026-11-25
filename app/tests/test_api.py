import os
import tempfile

# Banco temporário exclusivo desta execução de testes
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "teste_tarefas.db")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def nova(titulo, **extra):
    r = client.post("/api/tarefas", json={"titulo": titulo, **extra})
    assert r.status_code == 201
    return r.json()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_criar_e_listar():
    t = nova("estudar nuvem")
    assert t["prioridade"] == "media"
    assert t["feita"] is False
    titulos = [x["titulo"] for x in client.get("/api/tarefas").json()]
    assert "estudar nuvem" in titulos


def test_criar_com_prioridade_e_prazo():
    t = nova("entregar projeto", prioridade="alta", prazo="2026-12-01")
    assert t["prioridade"] == "alta"
    assert t["prazo"] == "2026-12-01"


def test_titulo_vazio():
    assert client.post("/api/tarefas", json={"titulo": "  "}).status_code == 400


def test_prioridade_invalida():
    r = client.post("/api/tarefas", json={"titulo": "x", "prioridade": "urgentissima"})
    assert r.status_code == 422


def test_concluir_e_reabrir():
    t = nova("tarefa para concluir")
    r = client.patch(f"/api/tarefas/{t['id']}", json={"feita": True})
    assert r.status_code == 200 and r.json()["feita"] is True
    r = client.patch(f"/api/tarefas/{t['id']}", json={"feita": False})
    assert r.json()["feita"] is False


def test_editar_tarefa():
    t = nova("titulo antigo")
    r = client.patch(f"/api/tarefas/{t['id']}",
                     json={"titulo": "titulo novo", "prioridade": "baixa", "prazo": "2026-12-25"})
    assert r.status_code == 200
    d = r.json()
    assert (d["titulo"], d["prioridade"], d["prazo"]) == ("titulo novo", "baixa", "2026-12-25")
    # prazo pode ser removido
    r = client.patch(f"/api/tarefas/{t['id']}", json={"prazo": None})
    assert r.json()["prazo"] is None


def test_editar_com_titulo_vazio():
    t = nova("nao pode ficar vazio")
    assert client.patch(f"/api/tarefas/{t['id']}", json={"titulo": " "}).status_code == 400


def test_atualizar_inexistente():
    assert client.patch("/api/tarefas/99999", json={"feita": True}).status_code == 404


def test_filtro_por_status():
    a = nova("filtro-pendente-xyz")
    b = nova("filtro-concluida-xyz")
    client.patch(f"/api/tarefas/{b['id']}", json={"feita": True})
    pend = [x["id"] for x in client.get("/api/tarefas?status=pendentes").json()]
    conc = [x["id"] for x in client.get("/api/tarefas?status=concluidas").json()]
    assert a["id"] in pend and b["id"] not in pend
    assert b["id"] in conc and a["id"] not in conc


def test_busca_por_texto():
    nova("comprar abacaxi-unico")
    achadas = client.get("/api/tarefas?busca=abacaxi-unico").json()
    assert len(achadas) == 1 and achadas[0]["titulo"] == "comprar abacaxi-unico"


def test_ordenacao_por_prioridade():
    baixa = nova("ord-baixa", prioridade="baixa")
    alta = nova("ord-alta", prioridade="alta")
    ids = [x["id"] for x in client.get("/api/tarefas?status=pendentes").json()]
    assert ids.index(alta["id"]) < ids.index(baixa["id"])


def test_resumo():
    nova("atrasada-resumo", prazo="2020-01-01")
    r = client.get("/api/resumo?hoje=2026-11-24").json()
    assert r["total"] == r["pendentes"] + r["concluidas"]
    assert r["atrasadas"] >= 1


def test_remover_tarefa():
    t = nova("tarefa para remover")
    assert client.delete(f"/api/tarefas/{t['id']}").status_code == 200
    assert client.delete(f"/api/tarefas/{t['id']}").status_code == 404


def test_limpar_concluidas():
    feita = nova("limpar-feita")
    aberta = nova("limpar-aberta")
    client.patch(f"/api/tarefas/{feita['id']}", json={"feita": True})
    r = client.delete("/api/tarefas/concluidas")
    assert r.status_code == 200 and r.json()["removidas"] >= 1
    ids = [x["id"] for x in client.get("/api/tarefas").json()]
    assert feita["id"] not in ids and aberta["id"] in ids


def test_metricas():
    nova("gera metrica")
    texto = client.get("/metrics").text
    assert "http_requests_total" in texto
    assert "tarefas_criadas_total" in texto
