# analisis_excel_universal_es.py
import pandas as pd
import numpy as np
import re
from pathlib import Path
import matplotlib.pyplot as plt
from scipy import stats
 
# CONFIGURACIÓN

archivo_excel = Path("04_ANEXO_3_BaseDatosVentasCar_2.xlsx")  
max_row_to_search = 15                  
trim_frac = 0.10                        
bins_por_defecto = 10
max_columnas_a_graficar = 12          

# UTILIDADES

def limpiar_texto(s):
    if pd.isna(s):
        return ""
    s = str(s).replace("\xa0", " ").replace("\ufeff", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s
 
def detectar_fila_header(raw_df, max_row=max_row_to_search):
    """
    Heurística simple: busca una fila con "mucho texto" (no numérico) que parezca encabezado.
    """
    mejor_fila = 0
    mejor_score = -1
 
    for r in range(min(max_row, len(raw_df))):
        fila = raw_df.iloc[r].tolist()
       
        score = 0
        for v in fila:
            t = limpiar_texto(v)
            if t == "" or t.lower() == "nan":
                continue
           
            try:
                float(t)
               
            except:
                score += 1
 
        if score > mejor_score:
            mejor_score = score
            mejor_fila = r
 
    return mejor_fila
 
def media_recortada(datos, porcentaje=trim_frac):
    porcentaje = max(0.0, min(0.49, float(porcentaje)))
    return stats.trim_mean(datos, porcentaje)
 
def mediana_recortada(datos, porcentaje=trim_frac):
    datos = np.asarray(datos)
    n = len(datos)
    k = int(n * porcentaje)
    if n - 2 * k <= 0:
        return np.median(datos)
    return np.median(np.sort(datos)[k:n-k])
 
def tabla_frecuencias(datos, bins=bins_por_defecto):
    frecuencias, limites = np.histogram(datos, bins=bins)
    marcas = (limites[:-1] + limites[1:]) / 2
    fr_relativa = frecuencias / len(datos)
    fr_acumulada = np.cumsum(frecuencias)
    fr_rel_acum = np.cumsum(fr_relativa)
 
    return pd.DataFrame({
        "Inicio": limites[:-1],
        "Fin": limites[1:],
        "Marca de clase": marcas,
        "Frecuencia": frecuencias,
        "Frecuencia relativa": fr_relativa,
        "Frecuencia acumulada": fr_acumulada,
        "Frecuencia relativa acumulada": fr_rel_acum
    })
 
def analisis_estadistico_columna(serie, nombre):
    datos = pd.to_numeric(serie, errors="coerce").dropna().astype(float).values
 
    if len(datos) == 0:
        return None
 
    resultados = {
        "Variable": nombre,
        "n": len(datos),
        "Media": float(np.mean(datos)),
        "Mediana": float(np.median(datos)),
        "Media recortada 10%": float(media_recortada(datos)),
        "Mediana recortada 10%": float(mediana_recortada(datos)),
        "Moda(s)": pd.Series(datos).mode().tolist(),
        "Varianza muestral": float(np.var(datos, ddof=1)) if len(datos) > 1 else float("nan"),
        "Desv. estándar muestral": float(np.std(datos, ddof=1)) if len(datos) > 1 else float("nan")
    }
 
    return resultados, datos
 
def graficar_histogramas(datos, nombre, bins=bins_por_defecto):
    plt.figure()
    plt.hist(datos, bins=bins)
    plt.title(f"Histograma - {nombre}")
    plt.xlabel(nombre)
    plt.ylabel("Frecuencia")
    plt.tight_layout()
    plt.show()
    plt.close()
 
    plt.figure()
    plt.hist(datos, bins=bins, cumulative=True)
    plt.title(f"Histograma acumulado - {nombre}")
    plt.xlabel(nombre)
    plt.ylabel("Frecuencia acumulada")
    plt.tight_layout()
    plt.show()
    plt.close()

# LECTURA DEL EXCEL (ROBUSTA)

if not archivo_excel.exists():
    raise SystemExit(f"❌ No se encontró el archivo: {archivo_excel.resolve()}")
 
raw = pd.read_excel(archivo_excel, header=None)
print("✅ Vista rápida (primeras filas, sin encabezado):")
print(raw.head(8))
 
fila_header = detectar_fila_header(raw)
print(f"\n✅ Fila detectada como encabezado probable: {fila_header}")
 
df = pd.read_excel(archivo_excel, header=fila_header)
 
 
df.columns = [limpiar_texto(c) if limpiar_texto(c) != "" else f"Columna_{i}" for i, c in enumerate(df.columns)]
print("\n✅ Columnas detectadas:")
print(list(df.columns))

# DETECTAR COLUMNAS NUMÉRICAS

df_num = df.copy()
 
 
for c in df_num.columns:
    df_num[c] = pd.to_numeric(df_num[c], errors="coerce")
 
 
columnas_numericas = [c for c in df_num.columns if df_num[c].notna().sum() >= 5]
 
if not columnas_numericas:
    raise SystemExit("❌ No se detectaron columnas numéricas suficientes (mínimo 5 valores numéricos por columna).")
 
print("\n✅ Columnas numéricas detectadas para análisis:")
for c in columnas_numericas:
    print("-", c)

# ANÁLISIS POR COLUMNA

print("\n" + "=" * 70)
print("ANÁLISIS ESTADÍSTICO AUTOMÁTICO (TODAS LAS COLUMNAS NUMÉRICAS)")
print("=" * 70)
 
resultados_globales = []
datos_por_columna = {}
 
for idx, col in enumerate(columnas_numericas):
    salida = analisis_estadistico_columna(df[col], col)
    if salida is None:
        continue
 
    resultados, datos = salida
    resultados_globales.append(resultados)
    datos_por_columna[col] = datos
 
    print("\n" + "=" * 60)
    print(f"VARIABLE: {col}")
    print("=" * 60)
    print(f"Cantidad de datos (n): {resultados['n']}")
    print("Media:", resultados["Media"])
    print("Mediana:", resultados["Mediana"])
    print("Media recortada 10%:", resultados["Media recortada 10%"])
    print("Mediana recortada 10%:", resultados["Mediana recortada 10%"])
    print("Moda(s):", resultados["Moda(s)"])
    print("Varianza muestral:", resultados["Varianza muestral"])
    print("Desv. estándar muestral:", resultados["Desv. estándar muestral"])
 
    print("\n--- Tabla de frecuencias ---")
    print(tabla_frecuencias(datos))
 
   
    if idx < max_columnas_a_graficar:
        graficar_histogramas(datos, col)
    else:
        print("(Gráficas omitidas para esta variable por límite de columnas a graficar)")
 
# MATRIZ DE CORRELACIÓN / COVARIANZA

print("\n" + "=" * 70)
print("RELACIÓN ENTRE VARIABLES (MATRICES)")
print("=" * 70)
 
df_num_final = df_num[columnas_numericas].dropna(how="all")
 
 
corr = df_num_final.corr(method="pearson")
print("\n✅ Matriz de correlación de Pearson:")
print(corr)
 
 
cov = df_num_final.cov()
print("\n✅ Matriz de covarianza muestral:")
print(cov)
 
print("\n✅ Proceso finalizado correctamente (exit code 0).")
 