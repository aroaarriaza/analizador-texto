import json
import sys

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

datos = leer("textos/ejemplo.txt")
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

