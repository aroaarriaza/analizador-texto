import json
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path.home() / "py" / "llm" / ".env")

UMBRAL = 0.25


def cliente_ia():
    return OpenAI(
        api_key=os.environ["AI_GATEWAY_API_KEY"],
        base_url="https://ai-gateway.vercel.sh/v1",
    )


def buscar(conexion, pregunta, cuantos=3):
    embedding_pregunta = cliente_ia().embeddings.create(
        model="openai/text-embedding-3-small",
        input=[pregunta],
    ).data[0].embedding

    vector = json.dumps(embedding_pregunta)

    return conexion.execute("""
        SELECT 1 - (embedding <=> %s::vector), numero, texto
        FROM trozos
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (vector, vector, cuantos)).fetchall()


def responder(pregunta, encontrados):
    contexto = ""
    for puntuacion, numero, texto in encontrados:
        contexto += f"[Trozo {numero}]\n{texto}\n\n"

    respuesta = cliente_ia().chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        max_tokens=300,
        temperature=0,
        timeout=30,
        messages=[
            {"role": "system", "content":
                "Respondes SOLO con la información de los fragmentos que te doy. "
                "Si la respuesta no está ahí, empieza diciendo 'No lo encuentro en el texto' "
                "y a continuación cuenta lo más cercano que sí aparezca. "
                "Cita entre corchetes el trozo que has usado."},
            {"role": "user", "content": f"Fragmentos:\n\n{contexto}Pregunta: {pregunta}"},
        ],
    )
    return respuesta.choices[0].message.content


if len(sys.argv) < 2:
    print("Uso: python3 preguntar.py \"tu pregunta\"")
    sys.exit(1)

pregunta = sys.argv[1]

with psycopg.connect(os.environ["DATABASE_URL"]) as conexion:
    encontrados = buscar(conexion, pregunta)

print("Trozos más parecidos:")
for puntuacion, numero, texto in encontrados:
    print(f"  trozo {numero}: {puntuacion:.3f}")
print()

if encontrados[0][0] < UMBRAL:
    print("No lo encuentro en el texto (nada se parece lo suficiente).")
    sys.exit(0)

print(responder(pregunta, encontrados))
