# config.py
# Rutas del lakehouse y creacion de la sesion de Spark.
# Todos los scripts importan este archivo para no repetir codigo.

import os
import sys

# Carpeta base del proyecto (donde esta este archivo)
BASE = os.path.dirname(os.path.abspath(__file__))

# Zonas del lakehouse (simulan buckets de S3 / carpetas de HDFS)
RAW = os.path.join(BASE, "data", "raw")            # datos en bruto, tal como llegan
CLEAN = os.path.join(BASE, "data", "clean")        # datos limpios en Parquet
PREPARED = os.path.join(BASE, "data", "prepared")  # tablas listas para analisis

# Carpeta para reportes y graficos
SALIDA = os.path.join(BASE, "salida")


def crear_spark(nombre_app):
    """Crea una sesion de Spark en modo local."""
    # Spark tiene que usar el mismo Python con el que ejecutamos el script
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .appName(nombre_app)
        .master("local[*]")                             # usa todos los nucleos del PC
        .config("spark.sql.shuffle.partitions", "4")    # pocos datos, pocas particiones
        .config("spark.sql.session.timeZone", "America/Santiago")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")  # para que la consola no se llene de mensajes
    return spark


def titulo(texto):
    """Imprime un titulo para que la salida en consola se vea ordenada."""
    print()
    print("=" * 60)
    print(" " + texto)
    print("=" * 60)
