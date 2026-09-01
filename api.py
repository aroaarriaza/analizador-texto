from fastapi import FastAPI

from preguntar import analizar

app = FastAPI()


@app.get("/salud")
def salud():
    return {"estado": "ok"}


@app.get("/preguntar")
def hacer_pregunta(texto: str):
    return analizar(texto)
