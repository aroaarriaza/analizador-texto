import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

import vacias

# La clave vive en un único sitio, en ~/py/llm/.env — no se copia a este repo.
load_dotenv(Path.home() / "py" / "llm" / ".env")

def leer(ruta):
    try:
        with open(ruta, "r") as archivo:
            return archivo.read()
    except FileNotFoundError:
        print(f"No encuentro el archivo: {ruta}")
        sys.exit(1)


def contar_frecuencias(palabras):
    frecuencias = {}
    for palabra in palabras:
        palabra = palabra.lower().strip(".,;:()¿?¡!")
        if palabra in vacias.lista:
            continue
        if palabra in frecuencias:
            frecuencias[palabra] = frecuencias[palabra] + 1
        else:
            frecuencias[palabra] = 1
    return frecuencias


def trocear(palabras, tamano):
    trozos = []
    for i in range(0, len(palabras), tamano):
        trozo = palabras[i:i + tamano]
        trozos.append(" ".join(trozo))
    return trozos


def guardar(resultado, ruta):
    with open(ruta, "w") as archivo:
        json.dump(resultado, archivo, indent=2, ensure_ascii=False)

def conectar():
    conexion = sqlite3.connect("analisis.db")
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS analisis (
            id INTEGER PRIMARY KEY,
            archivo TEXT,
            palabras INTEGER,
            unicas INTEGER,
            fecha TEXT
        )
    """)
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS palabras (
            id INTEGER PRIMARY KEY,
            analisis_id INTEGER,
            palabra TEXT,
            veces INTEGER
        )
    """)
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS trozos (
            id INTEGER PRIMARY KEY,
            analisis_id INTEGER,
            numero INTEGER,
            texto TEXT,
            embedding TEXT
        )
    """)
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS resumenes (
            id INTEGER PRIMARY KEY,
            analisis_id INTEGER,
            numero INTEGER,
            resumen TEXT
        )
    """)
    conexion.commit()
    return conexion


def guardar_en_base(conexion, archivo, palabras, unicas, top5):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor = conexion.execute(
        "INSERT INTO analisis (archivo, palabras, unicas, fecha) VALUES (?, ?, ?, ?)",
        (archivo, palabras, unicas, fecha)
    )
    analisis_id = cursor.lastrowid

    filas = []
    for palabra, veces in top5:
        filas.append((analisis_id, palabra, veces))

    conexion.executemany(
        "INSERT INTO palabras (analisis_id, palabra, veces) VALUES (?, ?, ?)",
        filas
    )
    conexion.commit()
    return analisis_id

def cliente_ia():
    return OpenAI(
        api_key=os.environ["AI_GATEWAY_API_KEY"],
        base_url="https://ai-gateway.vercel.sh/v1",
    )


def calcular_embeddings(trozos):
    respuesta = cliente_ia().embeddings.create(
        model="openai/text-embedding-3-small",
        input=trozos,
    )
    return [dato.embedding for dato in respuesta.data]


def guardar_trozos(conexion, analisis_id, trozos, embeddings):
    filas = []
    for numero, (texto, embedding) in enumerate(zip(trozos, embeddings), 1):
        filas.append((analisis_id, numero, texto, json.dumps(embedding)))

    conexion.executemany(
        "INSERT INTO trozos (analisis_id, numero, texto, embedding) VALUES (?, ?, ?, ?)",
        filas
    )
    conexion.commit()


def resumir(trozos):
    cliente = cliente_ia()

    resumenes = []
    for numero, trozo in enumerate(trozos, 1):
        respuesta = cliente.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            max_tokens=100,
            temperature=0.3,
            timeout=30,
            messages=[
                {"role": "system", "content": "Resumes en una sola frase, en español. Solo la frase."},
                {"role": "user", "content": trozo},
            ],
        )
        resumenes.append((numero, respuesta.choices[0].message.content.strip()))
        print(f"  trozo {numero}/{len(trozos)} resumido")

    return resumenes


def guardar_resumenes(conexion, analisis_id, resumenes):
    filas = []
    for numero, resumen in resumenes:
        filas.append((analisis_id, numero, resumen))

    conexion.executemany(
        "INSERT INTO resumenes (analisis_id, numero, resumen) VALUES (?, ?, ?)",
        filas
    )
    conexion.commit()


if len(sys.argv) > 1:
    ruta = sys.argv[1]
else:
    ruta = "textos/ejemplo.txt"

datos = leer(ruta)

palabras = datos.split()
unicas = set(palabras)
frecuencias = contar_frecuencias(palabras)
ordenadas = sorted(frecuencias.items(), key=lambda pareja: pareja[1], reverse=True)
top5 = ordenadas[:5]
trozos = trocear(palabras, 100)

resultado = {
    "palabras_totales": len(palabras),
    "palabras_unicas": len(unicas),
    "top_5": top5,
    "trozos": trozos
}

guardar(resultado, "salida.json")

conexion = conectar()
analisis_id = guardar_en_base(conexion, ruta, len(palabras), len(unicas), top5)

print(f"Calculando embeddings de {len(trozos)} trozos...")
embeddings = calcular_embeddings(trozos)
guardar_trozos(conexion, analisis_id, trozos, embeddings)

print(f"Resumiendo {len(trozos)} trozos con IA...")
resumenes = resumir(trozos)
guardar_resumenes(conexion, analisis_id, resumenes)

conexion.close()

print(f"Análisis {analisis_id} guardado: {len(palabras)} palabras, {len(unicas)} únicas, {len(resumenes)} resúmenes")
