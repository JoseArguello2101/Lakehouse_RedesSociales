import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, CLEAN, crear_spark, titulo

from pyspark.sql import functions as F


def leer_publicaciones(spark):
    """Lee las paginas JSON y saca las publicaciones que vienen dentro de 'datos'."""
    paginas = spark.read.json(os.path.join(RAW, "publicaciones"))
    publicaciones = paginas.select(F.explode("datos").alias("p")).select("p.*")
    return publicaciones


def limpiar_publicaciones(df):
    """Corrige los errores de las publicaciones."""
    plataforma = F.lower(F.trim(F.col("plataforma")))
    df = df.withColumn(
        "plataforma",
        F.when(plataforma.isin("instagram", "ig"), "Instagram")
         .when(plataforma.isin("tiktok", "tik tok"), "TikTok")
         .when(plataforma.isin("x", "twitter"), "X")
         .otherwise("Otra")
    )

    df = df.filter(F.col("user_id").isNotNull())

    df = df.dropDuplicates(["id_post"])

    df = df.withColumn("fecha_hora", F.to_timestamp("fecha_hora", "yyyy-MM-dd HH:mm:ss"))
    df = df.filter(F.col("fecha_hora").isNotNull())

    for col in ["vistas", "likes", "comentarios", "compartidos"]:
        df = df.withColumn(col, F.coalesce(F.col(col), F.lit(0)))
        df = df.withColumn(col, F.when(F.col(col) < 0, 0).otherwise(F.col(col)))

    return df


def agregar_columnas(df):
    """Crea columnas nuevas que sirven para el analisis."""
    df = df.withColumn("fecha", F.to_date("fecha_hora"))
    df = df.withColumn("hora", F.hour("fecha_hora"))

    df = df.withColumn("hashtags", F.expr(r"regexp_extract_all(texto, '(#\\w+)', 1)"))

    df = df.withColumn("engagement", F.col("likes") + F.col("comentarios") + F.col("compartidos"))

    df = df.withColumn(
        "tasa_engagement",
        F.when(F.col("vistas") > 0, F.round(F.col("engagement") / F.col("vistas") * 100, 2))
         .otherwise(0.0)
    )
    return df


def leer_usuarios(spark):
    """Lee el CSV de usuarios y deja el pais escrito siempre igual."""
    usuarios = spark.read.csv(os.path.join(RAW, "usuarios"), header=True, inferSchema=True)
    pais = F.lower(F.trim(F.col("pais")))
    usuarios = usuarios.withColumn(
        "pais", F.when(pais.isin("chile", "cl"), "Chile").otherwise(F.initcap(pais))
    )
    return usuarios.select("user_id", "nombre_usuario", "pais", "seguidores")


if __name__ == "__main__":
    titulo("PASO 2 - LIMPIEZA CON PYSPARK")
    spark = crear_spark("Limpieza")

    crudo = leer_publicaciones(spark)
    total_antes = crudo.count()
    print("Publicaciones en RAW (antes):", total_antes)

    print("\nPlataformas como vienen en bruto:")
    crudo.groupBy("plataforma").count().orderBy("count", ascending=False).show()

    limpio = limpiar_publicaciones(crudo)
    limpio = agregar_columnas(limpio)

    usuarios = leer_usuarios(spark)
    limpio = limpio.join(usuarios, on="user_id", how="left")

    total_despues = limpio.count()
    print("Publicaciones limpias (despues):", total_despues)
    print("Filas eliminadas:", total_antes - total_despues)

    print("\nPlataformas despues de limpiar:")
    limpio.groupBy("plataforma").count().orderBy("plataforma").show()

    print("Ejemplo de datos limpios:")
    limpio.select("id_post", "plataforma", "fecha_hora", "hashtags",
                  "engagement", "tasa_engagement", "pais").show(5, truncate=False)

    destino = os.path.join(CLEAN, "publicaciones")
    limpio.write.mode("overwrite").partitionBy("plataforma").parquet(destino)
    print("Guardado en Parquet ->", destino)

    spark.stop()
