import logging, os, sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

DB_PATH = os.getenv("DB_PATH", "/data/tarefas.db")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("app")

app = FastAPI(title="Tarefas")
Instrumentator().instrument(app).expose(app)  # métricas em /metrics


class Tarefa(BaseModel):
    titulo: str


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            feita INTEGER DEFAULT 0)""")


init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/tarefas")
def listar():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM tarefas ORDER BY id DESC")]


@app.post("/api/tarefas", status_code=201)
def criar(t: Tarefa):
    if not t.titulo.strip():
        log.error("Tentativa de criar tarefa vazia")
        raise HTTPException(400, "Título obrigatório")
    with conn() as c:
        cur = c.execute("INSERT INTO tarefas (titulo) VALUES (?)", (t.titulo,))
    log.info("Tarefa criada id=%s", cur.lastrowid)
    return {"id": cur.lastrowid, "titulo": t.titulo, "feita": 0}


@app.put("/api/tarefas/{id}/concluir")
def concluir(id: int):
    with conn() as c:
        cur = c.execute("UPDATE tarefas SET feita=1 WHERE id=?", (id,))
    if cur.rowcount == 0:
        log.error("Tarefa %s não encontrada", id)
        raise HTTPException(404, "Não encontrada")
    log.info("Tarefa concluída id=%s", id)
    return {"ok": True}


@app.delete("/api/tarefas/{id}")
def remover(id: int):
    with conn() as c:
        c.execute("DELETE FROM tarefas WHERE id=?", (id,))
    log.info("Tarefa removida id=%s", id)
    return {"ok": True}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
