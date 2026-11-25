import logging, os, sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

DB_PATH = os.getenv("DB_PATH", "/data/tarefas.db")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("app")

app = FastAPI(title="Tarefas")
Instrumentator().instrument(app).expose(app)  # métricas em /metrics

# Métricas de negócio, além das métricas HTTP
TAREFAS_CRIADAS = Counter("tarefas_criadas_total", "Total de tarefas criadas")
TAREFAS_CONCLUIDAS = Counter("tarefas_concluidas_total", "Total de tarefas concluídas")

Prioridade = Literal["baixa", "media", "alta"]


class NovaTarefa(BaseModel):
    titulo: str = Field(max_length=200)
    prioridade: Prioridade = "media"
    prazo: Optional[date] = None


class AtualizaTarefa(BaseModel):
    titulo: Optional[str] = Field(default=None, max_length=200)
    feita: Optional[bool] = None
    prioridade: Optional[Prioridade] = None
    prazo: Optional[date] = None


@contextmanager
def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        with c:  # commit automático
            yield c
    finally:
        c.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            feita INTEGER DEFAULT 0)""")
        # Migração: bancos criados na primeira versão não têm estas colunas
        colunas = {r["name"] for r in c.execute("PRAGMA table_info(tarefas)")}
        if "prioridade" not in colunas:
            c.execute("ALTER TABLE tarefas ADD COLUMN prioridade TEXT NOT NULL DEFAULT 'media'")
        if "prazo" not in colunas:
            c.execute("ALTER TABLE tarefas ADD COLUMN prazo TEXT")


def para_dict(r):
    d = dict(r)
    d["feita"] = bool(d["feita"])
    return d


def buscar(id: int):
    with db() as c:
        r = c.execute("SELECT * FROM tarefas WHERE id=?", (id,)).fetchone()
    return para_dict(r) if r else None


init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/resumo")
def resumo(hoje: Optional[date] = None):
    """Contadores para o cabeçalho. 'hoje' vem do navegador (fuso do usuário)."""
    limite = (hoje or date.today()).isoformat()
    with db() as c:
        r = c.execute(
            """SELECT COUNT(*) AS total,
                      COALESCE(SUM(feita = 1), 0) AS concluidas,
                      COALESCE(SUM(feita = 0), 0) AS pendentes,
                      COALESCE(SUM(feita = 0 AND prazo IS NOT NULL AND prazo < ?), 0) AS atrasadas
               FROM tarefas""", (limite,)).fetchone()
    return dict(r)


@app.get("/api/tarefas")
def listar(status: Optional[Literal["pendentes", "concluidas"]] = None,
           busca: Optional[str] = None):
    condicoes, args = [], []
    if status == "pendentes":
        condicoes.append("feita = 0")
    elif status == "concluidas":
        condicoes.append("feita = 1")
    if busca and busca.strip():
        condicoes.append("titulo LIKE ?")
        args.append(f"%{busca.strip()}%")
    sql = "SELECT * FROM tarefas"
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += """ ORDER BY feita ASC,
               CASE prioridade WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END,
               prazo IS NULL, prazo ASC, id DESC"""
    with db() as c:
        return [para_dict(r) for r in c.execute(sql, args)]


@app.post("/api/tarefas", status_code=201)
def criar(t: NovaTarefa):
    titulo = t.titulo.strip()
    if not titulo:
        log.error("Tentativa de criar tarefa vazia")
        raise HTTPException(400, "Título obrigatório")
    prazo = t.prazo.isoformat() if t.prazo else None
    with db() as c:
        cur = c.execute(
            "INSERT INTO tarefas (titulo, prioridade, prazo) VALUES (?, ?, ?)",
            (titulo, t.prioridade, prazo))
    TAREFAS_CRIADAS.inc()
    log.info("Tarefa criada id=%s prioridade=%s", cur.lastrowid, t.prioridade)
    return buscar(cur.lastrowid)


# Esta rota precisa vir antes de /api/tarefas/{id}
@app.delete("/api/tarefas/concluidas")
def limpar_concluidas():
    with db() as c:
        cur = c.execute("DELETE FROM tarefas WHERE feita = 1")
    log.info("Tarefas concluídas removidas: %s", cur.rowcount)
    return {"removidas": cur.rowcount}


@app.patch("/api/tarefas/{id}")
def atualizar(id: int, t: AtualizaTarefa):
    atual = buscar(id)
    if atual is None:
        log.error("Tarefa %s não encontrada", id)
        raise HTTPException(404, "Tarefa não encontrada")

    campos = t.model_dump(exclude_unset=True)
    if not campos:
        raise HTTPException(400, "Nenhum campo para atualizar")
    if "titulo" in campos:
        titulo = (campos["titulo"] or "").strip()
        if not titulo:
            log.error("Tentativa de salvar tarefa %s com título vazio", id)
            raise HTTPException(400, "Título obrigatório")
        campos["titulo"] = titulo
    if "feita" in campos:
        if campos["feita"] is None:
            raise HTTPException(400, "Valor inválido para 'feita'")
        campos["feita"] = int(campos["feita"])
    if "prioridade" in campos and campos["prioridade"] is None:
        raise HTTPException(400, "Valor inválido para 'prioridade'")
    if "prazo" in campos:
        campos["prazo"] = campos["prazo"].isoformat() if campos["prazo"] else None

    # Os nomes das colunas vêm dos campos do modelo (conjunto fixo), nunca do usuário
    sets = ", ".join(f"{k} = ?" for k in campos)
    with db() as c:
        c.execute(f"UPDATE tarefas SET {sets} WHERE id = ?", [*campos.values(), id])

    if campos.get("feita") == 1 and not atual["feita"]:
        TAREFAS_CONCLUIDAS.inc()
    log.info("Tarefa atualizada id=%s campos=%s", id, ",".join(campos))
    return buscar(id)


@app.delete("/api/tarefas/{id}")
def remover(id: int):
    with db() as c:
        cur = c.execute("DELETE FROM tarefas WHERE id = ?", (id,))
    if cur.rowcount == 0:
        log.error("Tarefa %s não encontrada", id)
        raise HTTPException(404, "Tarefa não encontrada")
    log.info("Tarefa removida id=%s", id)
    return {"ok": True}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
