# Paso 3: zona preparada, tablas resumen para analisis
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CLEAN, PREPARED, crear_spark
from pyspark.sql import functions as F

spark = crear_spark("zona_preparada")

# leer datos limpios del paso 2
df = spark.read.parquet(CLEAN + "/publicaciones")
print("Total publicaciones:", df.count())
df.printSchema()

# tabla 1: publicaciones por dia y plataforma
resumen = df.groupBy("fecha", "plataforma").agg(
    F.count("id_post").alias("publicaciones"),
    F.sum("vistas").alias("vistas"),
    F.round(F.avg("engagement"), 2).alias("engagement_prom")
).orderBy("fecha", "plataforma")

resumen.show(21)
resumen.write.mode("overwrite").parquet(PREPARED + "/resumen_diario")

# tabla 2: hashtags mas usados (explode separa la lista)
hashtags = df.select(F.explode("hashtags").alias("hashtag"), "engagement")

top_hashtags = hashtags.groupBy("hashtag").agg(
    F.count("*").alias("usos"),
    F.round(F.avg("engagement"), 2).alias("engagement_prom")
).orderBy(F.desc("usos"))

top_hashtags.show(10)
top_hashtags.write.mode("overwrite").parquet(PREPARED + "/top_hashtags")

# tabla 3: usuarios con mas engagement
ranking = df.groupBy("user_id", "nombre_usuario", "pais", "seguidores").agg(
    F.count("id_post").alias("publicaciones"),
    F.sum("engagement").alias("engagement_total")
).orderBy(F.desc("engagement_total"))

ranking.show(10)
ranking.write.mode("overwrite").parquet(PREPARED + "/ranking_usuarios")

# tabla 4: actividad por hora
por_hora = df.groupBy("plataforma", "hora").agg(
    F.count("id_post").alias("publicaciones"),
    F.round(F.avg("engagement"), 2).alias("engagement_prom")
).orderBy("plataforma", "hora")

por_hora.show(24)
por_hora.write.mode("overwrite").parquet(PREPARED + "/actividad_hora")

# tabla 5: engagement segun tipo de contenido
contenido = df.groupBy("plataforma", "tipo_contenido").agg(
    F.count("id_post").alias("publicaciones"),
    F.round(F.avg("engagement"), 2).alias("engagement_prom"),
    F.round(F.avg("tasa_engagement"), 2).alias("tasa_prom")
).orderBy(F.desc("engagement_prom"))

contenido.show()
contenido.write.mode("overwrite").parquet(PREPARED + "/tipo_contenido")

print("Tablas guardadas en", PREPARED)
spark.stop()