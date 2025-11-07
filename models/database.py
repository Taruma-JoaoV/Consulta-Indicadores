import pymssql
from config import DB_CONFIG
import os

def conectar_banco():
    try:
        conn_str = os.getenv('DATABASE_URL')
        server, user, password, database = conn_str.split(';')
        conexao = pymssql.connect(
            server=server,
            user=user,
            password=password,
            database=database
        )
    except Exception as e:
        print("Erro ao conectar:", e)
        return None
