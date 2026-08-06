import sqlite3

conexion = sqlite3.connect("analisis.db")

print("--- Mis análisis, el más largo primero ---")
for fila in conexion.execute("""
    SELECT archivo, palabras, unicas, fecha
    FROM analisis
    ORDER BY palabras DESC
"""):
    print(fila)

print()
print("--- Top 5 del último análisis ---")
for fila in conexion.execute("""
    SELECT palabras.palabra, palabras.veces
    FROM palabras
    JOIN analisis ON palabras.analisis_id = analisis.id
    WHERE analisis.id = (SELECT MAX(id) FROM analisis)
    ORDER BY palabras.veces DESC
"""):
    print(fila)

print()
print("--- Resumen de todo ---")
for fila in conexion.execute("""
    SELECT COUNT(*), SUM(palabras)
    FROM analisis
"""):
    print(fila)

print()
print("--- Las 3 palabras más repetidas de todos mis textos ---")
for fila in conexion.execute("""
    SELECT palabra, SUM(veces)
    FROM palabras
    GROUP BY palabra
    ORDER BY SUM(veces) DESC
    LIMIT 3
"""):
    print(fila)


conexion.close()

