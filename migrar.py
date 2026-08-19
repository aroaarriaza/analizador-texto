import json
import os
import sqlite3
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path.home() / "py" / "llm" / ".env")

sqlite = sqlite3.connect("analisis.db")
filas = sqlite.execute("SELECT analisis_id, numero, texto, embedding FROM trozos").fetchall()
sqlite.close()

with psycopg.connect(os.environ["DATABASE_URL"]) as postgres:
    postgres.execute("TRUNCATE trozos")

    for analisis_id, numero, texto, embedding in filas:
        postgres.execute(
            "INSERT INTO trozos (analisis_id, numero, texto, embedding) VALUES (%s, %s, %s, %s)",
            (analisis_id, numero, texto, json.dumps(json.loads(embedding))),
        )

    postgres.commit()

print(f"{len(filas)} trozos copiados a Supabase")
