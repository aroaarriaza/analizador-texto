# Analizador de texto

Programa en Python que lee un archivo de texto, lo analiza, lo resume con IA y
permite **hacerle preguntas en lenguaje natural**.

Empezó como un contador de palabras y ha ido creciendo hasta ser un **RAG**
completo (*Retrieval Augmented Generation*): la técnica que permite que un modelo
de IA responda sobre documentos que nunca ha visto.

## Qué hace

**Al analizar un texto** (`analizador.py`):

1. Cuenta palabras totales y distintas, ignorando puntuación y *stopwords*
2. Saca las 5 palabras más repetidas
3. Trocea el texto en fragmentos de 100 palabras
4. Calcula el **embedding** de cada fragmento (una llamada en lote)
5. Pide al modelo un **resumen de una frase** por fragmento
6. Guarda todo en SQLite

**Al preguntar** (`preguntar.py`):

1. Convierte la pregunta en un embedding
2. Busca en PostgreSQL los 3 fragmentos más parecidos, con **pgvector**
3. Si nada supera el umbral de parecido, responde que no lo sabe **sin llamar al modelo**
4. Si lo supera, manda esos fragmentos al modelo y responde citando el fragmento usado

## Cómo se usa

```bash
python3 analizador.py textos/ejemplo.txt
python3 preguntar.py "¿qué problema hay con los créditos?"
python3 historial.py
```

```
$ python3 preguntar.py "¿qué problema hay con los créditos?"
Trozos más parecidos:
  trozo 5: 0.429
  trozo 6: 0.360
  trozo 2: 0.264

Según el texto, el problema es que ["Si el mismo usuario lanza varias
generaciones a la vez desde dos pestañas distintas, un descuento mal
implementado puede permitir gastar más crédito del disponible"] [Trozo 5].
```

## Decisiones

**Los embeddings se piden en lote, los resúmenes uno a uno.** Seis fragmentos son
una sola llamada de embeddings pero seis de resumen, porque cada resumen necesita
su propia respuesta. Con miles de fragmentos, la diferencia es de minutos a horas.

**Dos defensas contra las alucinaciones.** Un umbral de parecido que evita llamar
al modelo cuando nada encaja, y un *system prompt* que obliga a responder solo con
los fragmentos recuperados y a citar cuál se ha usado.

**Un umbral alto no garantiza una respuesta.** A la pregunta *«¿cuántas
descripciones hay?»* la búsqueda devuelve fragmentos con parecido 0.59 —los más
altos de todo el proyecto— y aun así no hay respuesta posible: contar no es buscar.
Eso lo resuelve el prompt, no el umbral.

**La búsqueda vive en la base de datos, no en Python.** La primera versión traía
todas las filas a Python y comparaba en un bucle. Funciona con cientos de
fragmentos y es inviable con cientos de miles. Con `pgvector`, el `ORDER BY` y el
`LIMIT` los resuelve PostgreSQL, y solo viajan las 3 filas que interesan.

**El modelo de embeddings tiene que hablar tu idioma.** Con `all-MiniLM-L6-v2`
(solo inglés) sobre texto en español, las puntuaciones salían invertidas sin dar
ningún error. Es un fallo silencioso: números plausibles y equivocados.

## Archivos

| Archivo | Qué contiene |
|---|---|
| `analizador.py` | Análisis, embeddings y resúmenes |
| `preguntar.py` | La búsqueda vectorial y la respuesta |
| `historial.py` | Consultas sobre los análisis guardados |
| `migrar.py` | Copia los fragmentos de SQLite a Supabase |
| `vacias.py` | *Stopwords* en español |
| `textos/ejemplo.txt` | Texto de prueba |

## Requisitos

```bash
pip install openai python-dotenv "psycopg[binary]"
```

Dos variables de entorno:

| Variable | Para qué |
|---|---|
| `AI_GATEWAY_API_KEY` | Embeddings y respuestas, por Vercel AI Gateway |
| `DATABASE_URL` | PostgreSQL con la extensión `vector` activada |

La tabla y el índice:

```sql
create extension if not exists vector;

create table trozos (
  id bigserial primary key,
  analisis_id int,
  numero int,
  texto text,
  embedding vector(1536)
);

create index on trozos using hnsw (embedding vector_cosine_ops);
```
