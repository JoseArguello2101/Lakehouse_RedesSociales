# Paso 4: consultas y graficos sobre la zona preparada
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CLEAN, PREPARED, SALIDA, crear_spark
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs(SALIDA, exist_ok=True)

# consulta con Spark SQL sobre los datos limpios
spark = crear_spark("consultas")
df = spark.read.parquet(CLEAN + "/publicaciones")
df.createOrReplaceTempView("publicaciones")

por_plataforma = spark.sql("""
    SELECT plataforma,
           COUNT(*) AS publicaciones,
           ROUND(AVG(engagement), 2) AS engagement_prom,
           ROUND(AVG(tasa_engagement), 2) AS tasa_prom
    FROM publicaciones
    GROUP BY plataforma
    ORDER BY engagement_prom DESC
""")
por_plataforma.show()

# pasamos el resultado a pandas para graficar
plataformas = por_plataforma.toPandas()
spark.stop()

# leer las tablas de la zona preparada con pandas
resumen = pd.read_parquet(PREPARED + "/resumen_diario")
hashtags = pd.read_parquet(PREPARED + "/top_hashtags")
por_hora = pd.read_parquet(PREPARED + "/actividad_hora")

# respuestas a las preguntas del analisis
print("Plataforma con mas engagement:", plataformas.iloc[0]["plataforma"])
print("Hashtag mas usado:", hashtags.sort_values("usos", ascending=False).iloc[0]["hashtag"])
print("Hashtag con mas engagement:", hashtags.sort_values("engagement_prom", ascending=False).iloc[0]["hashtag"])

total_hora = por_hora.groupby("hora")["publicaciones"].sum()
print("Hora con mas publicaciones:", total_hora.idxmax(), "hrs")

por_dia = resumen.groupby("fecha")["publicaciones"].sum()
print("\nPublicaciones por dia:")
print(por_dia)

# grafico 1: engagement promedio por plataforma
plt.figure()
plt.bar(plataformas["plataforma"], plataformas["engagement_prom"], color=["black", "purple", "gray"])
plt.title("Engagement promedio por plataforma")
plt.ylabel("engagement promedio")
plt.savefig(SALIDA + "/1_engagement_plataforma.png")
plt.close()

# grafico 2: publicaciones por dia (se ve el peak del 18)
tabla_dia = resumen.pivot(index="fecha", columns="plataforma", values="publicaciones")
tabla_dia.plot(marker="o")
plt.title("Publicaciones por dia - semana Fiestas Patrias")
plt.ylabel("publicaciones")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(SALIDA + "/2_publicaciones_por_dia.png")
plt.close()

# grafico 3: hashtags con mas engagement
top10 = hashtags.sort_values("engagement_prom").tail(10)
plt.figure()
plt.barh(top10["hashtag"], top10["engagement_prom"])
plt.title("Top 10 hashtags por engagement promedio")
plt.tight_layout()
plt.savefig(SALIDA + "/3_top_hashtags.png")
plt.close()

# grafico 4: mapa de calor hora x plataforma
calor = por_hora.pivot(index="plataforma", columns="hora", values="publicaciones")
plt.figure(figsize=(12, 3))
plt.imshow(calor, cmap="YlOrRd", aspect="auto")
plt.yticks(range(len(calor.index)), calor.index)
plt.xticks(range(24), range(24))
plt.colorbar(label="publicaciones")
plt.title("Publicaciones por hora y plataforma")
plt.xlabel("hora")
plt.tight_layout()
plt.savefig(SALIDA + "/4_mapa_calor_horas.png")
plt.close()

# reporte final en csv
plataformas.to_csv(SALIDA + "/reporte_plataformas.csv", index=False)
resumen.to_csv(SALIDA + "/reporte_diario.csv", index=False)
print("\nGraficos y reportes guardados en", SALIDA)