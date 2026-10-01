import os
import sys
import csv
import json
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW, titulo

random.seed(42)

CANT_USUARIOS = 300
PUBLICACIONES_POR_DIA = 800
FECHA_INICIO = datetime(2026, 9, 14) 
DIAS = 7

PLATAFORMAS = ["Instagram", "TikTok", "X"]
PLATAFORMAS_SUCIAS = {
    "Instagram": ["Instagram", "instagram", "INSTAGRAM", " Instagram ", "IG"],
    "TikTok": ["TikTok", "tiktok", "Tik Tok", "TIKTOK "],
    "X": ["X", "x", "Twitter", "twitter"],
}
TIPOS_CONTENIDO = {
    "Instagram": ["foto", "reel", "carrusel", "historia"],
    "TikTok": ["video"],
    "X": ["texto", "foto", "video"],
}
HASHTAGS = ["#chile", "#santiago", "#futbol", "#musica", "#comida", "#viajes",
            "#tecnologia", "#moda", "#gaming", "#humor", "#deporte", "#valparaiso"]
HASHTAGS_18 = ["#fiestaspatrias", "#dieciocho", "#empanadas", "#cueca", "#fonda"]
PAISES = ["Chile", "chile", "CL", "Argentina", "Peru", "Mexico", "Colombia"]

PESO_HORAS = [1, 1, 1, 1, 1, 1, 2, 3, 4, 4, 5, 6, 7, 6, 5, 5, 6, 7, 8, 10, 11, 10, 7, 3]

def generar_usuarios():
    """Genera la lista de usuarios (fuente CSV)."""
    usuarios = []
    for i in range(1, CANT_USUARIOS + 1):
        registro = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 2000))
        usuarios.append({
            "user_id": i,
            "nombre_usuario": "usuario_" + str(i),
            "pais": random.choice(PAISES),
            "fecha_registro": registro.strftime("%Y-%m-%d"),
            # pocos usuarios tienen muchos seguidores (como en la vida real)
            "seguidores": int(random.paretovariate(1.2) * 200),
        })
    return usuarios


def calcular_metricas(plataforma, es_18):
    """Genera vistas, likes, comentarios y compartidos segun la plataforma."""
    if plataforma == "TikTok":
        vistas = random.randint(500, 50000)
    elif plataforma == "Instagram":
        vistas = random.randint(200, 20000)
    else:
        vistas = random.randint(50, 8000)

    if es_18:
        vistas = int(vistas * 1.8)  

    likes = int(vistas * random.uniform(0.02, 0.12))
    comentarios = int(likes * random.uniform(0.01, 0.15))
    compartidos = int(likes * random.uniform(0.0, 0.10))
    return vistas, likes, comentarios, compartidos


def simular_api(dia, id_inicial):
    """
    Simula la respuesta de una API de redes sociales para un dia.
    Devuelve una lista de "paginas", cada una con 100 publicaciones.
    """
    fecha = FECHA_INICIO + timedelta(days=dia)
    es_18 = fecha.day in (17, 18, 19)

    publicaciones = []
    cantidad = PUBLICACIONES_POR_DIA * 2 if es_18 else PUBLICACIONES_POR_DIA
    for n in range(cantidad):
        plataforma = random.choice(PLATAFORMAS)
        hora = random.choices(range(24), weights=PESO_HORAS)[0]
        fecha_hora = fecha.replace(hour=hora, minute=random.randint(0, 59),
                                   second=random.randint(0, 59))

        tags = random.sample(HASHTAGS, random.randint(0, 3))
        if es_18 and random.random() < 0.6:
            tags += random.sample(HASHTAGS_18, random.randint(1, 2))

        vistas, likes, comentarios, compartidos = calcular_metricas(plataforma, es_18)

        pub = {
            "id_post": "P" + str(id_inicial + n),
            "user_id": random.randint(1, CANT_USUARIOS),
            "plataforma": random.choice(PLATAFORMAS_SUCIAS[plataforma]),
            "tipo_contenido": random.choice(TIPOS_CONTENIDO[plataforma]),
            "fecha_hora": fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
            "texto": "Publicacion de prueba " + " ".join(tags),
            "vistas": vistas,
            "likes": likes,
            "comentarios": comentarios,
            "compartidos": compartidos,
        }

        r = random.random()
        if r < 0.02:
            pub["user_id"] = None                  
        elif r < 0.04:
            pub["fecha_hora"] = "fecha_invalida"   
        elif r < 0.06:
            pub["likes"] = -1 * pub["likes"]      
        elif r < 0.08:
            pub["comentarios"] = None              

        publicaciones.append(pub)

    
        if random.random() < 0.03:
            publicaciones.append(dict(pub))

    paginas = []
    for i in range(0, len(publicaciones), 100):
        paginas.append({
            "pagina": i // 100 + 1,
            "fecha_consulta": fecha.strftime("%Y-%m-%d"),
            "datos": publicaciones[i:i + 100],
        })
    return fecha, paginas, id_inicial + cantidad


def guardar_usuarios(usuarios):
    carpeta = os.path.join(RAW, "usuarios")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "usuarios.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=usuarios[0].keys())
        escritor.writeheader()
        escritor.writerows(usuarios)
    print("Usuarios guardados:", len(usuarios), "->", ruta)


def guardar_publicaciones():
    """Llama a la API simulada dia por dia y guarda cada pagina como JSON."""
    total = 0
    id_actual = 1
    for dia in range(DIAS):
        fecha, paginas, id_actual = simular_api(dia, id_actual)

        carpeta = os.path.join(RAW, "publicaciones", "fecha=" + fecha.strftime("%Y-%m-%d"))
        os.makedirs(carpeta, exist_ok=True)

        for p in paginas:
            ruta = os.path.join(carpeta, "pagina_" + str(p["pagina"]).zfill(3) + ".json")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(p, f, ensure_ascii=False)
            total += len(p["datos"])

        print(fecha.strftime("%Y-%m-%d"), "->", len(paginas), "paginas JSON")
    print("Publicaciones guardadas en bruto:", total)


if __name__ == "__main__":
    titulo("PASO 1 - INGESTA A LA ZONA RAW")
    guardar_usuarios(generar_usuarios())
    guardar_publicaciones()
    print("\nListo. Revisa la carpeta:", RAW)
