import json
import sqlite3
import sys
from datetime import datetime

import vacias

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
conexion.close()

print(f"Análisis {analisis_id} guardado: {len(palabras)} palabras, {len(unicas)} únicas")
