import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement
from models.models import Occurrence 
from database import engine
import json


path = "/home/alisson/projetos/issafe/backend/issafe/seed/coordenadas_formatadas.json"
tamanho_lote = 1000

def ler_em_lotes(path, tamanho_lote):
    with open(path, "r", encoding="utf-8") as f:
        dados = json.load(f)
        for i in range(0, len(dados), tamanho_lote):
            yield dados[i:i + tamanho_lote]


with Session(engine) as session:
    for lote in ler_em_lotes(path, tamanho_lote):
        registros = []
        for d in lote:
            lat, lon = d["local"]
            point = WKTElement(f"POINT({lon} {lat})", srid=4326)
            registros.append({
                "user_uuid": d["user_uuid"],
                "type": d["type"],
                "description": d["description"],
                "coordinates": d["local"],
                "local": point
            })

        session.bulk_insert_mappings(Occurrence, registros)
        session.commit()
        print(f"Lote com {len(registros)} registros inserido com sucesso.")