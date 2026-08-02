# Analizador de texto

Programa en Python que lee un archivo de texto y devuelve un análisis en formato JSON:
cuenta palabras, saca las más repetidas y trocea el texto en fragmentos.

Es un proyecto de aprendizaje, pero el troceado en fragmentos es el primer paso de
**RAG** (*Retrieval Augmented Generation*): la técnica que se usa para que un modelo
de IA pueda responder sobre documentos que no conoce.

## Qué hace

1. Lee el archivo de texto
2. Cuenta el total de palabras y cuántas son distintas
3. Cuenta cuántas veces aparece cada palabra, ignorando mayúsculas, puntuación y
   *stopwords* (`de`, `la`, `que`, `y`...)
4. Ordena por frecuencia y saca el top 5
5. Trocea el texto en fragmentos de 100 palabras
6. Guarda todo en `salida.json`

## Cómo se usa

```bash
python3 analizador.py
```

Analiza `textos/ejemplo.txt` y escribe el resultado en `salida.json`.
Para analizar otro archivo, cambia la ruta en la llamada a `leer()`.

No necesita instalar nada: solo usa la librería estándar de Python.

## Resultado

```json
{
  "palabras_totales": 588,
  "palabras_unicas": 322,
  "top_5": [
    ["producto", 9],
    ["texto", 7],
    ["tienda", 5],
    ["descripción", 4],
    ["datos", 4]
  ],
  "trozos": ["..."]
}
```

Sin limpiar el texto, el top 5 sería `de`, `que`, `el`, `un`, `la` — palabras que no
dicen nada del contenido. Por eso se filtran las *stopwords* y se normalizan
mayúsculas y puntuación antes de contar.

## Archivos

| Archivo | Qué contiene |
|---|---|
| `analizador.py` | El programa |
| `vacias.py` | Lista de *stopwords* en español |
| `textos/ejemplo.txt` | Texto de prueba |
| `salida.json` | Resultado (lo genera el programa) |

## Estructura del código

Cuatro funciones y un programa que las encadena:

```python
def leer(ruta): ...                    # abre el archivo (maneja que no exista)
def contar_frecuencias(palabras): ...  # diccionario palabra → veces
def trocear(palabras, tamano): ...     # fragmentos de N palabras
def guardar(resultado, ruta): ...      # escribe el JSON
```

Si el archivo de entrada no existe, el programa avisa con un mensaje claro y termina
con código de salida `1` en vez de estrellarse.
