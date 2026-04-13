from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(
    title="Verifiq by Dini Inc.",
    description="Plataforma de enriquecimento de dados — 216M PF, 662M telefones, 878M endereços",
    version="1.0.0",
)

base = os.path.dirname(__file__)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(base, "static")),
    name="static",
)


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(os.path.join(base, "templates", "index.html"))


@app.get("/health")
def health():
    return {"status": "ok", "service": "Verifiq by Dini Inc."}
