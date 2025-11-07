import pymssql
from config import DB_CONFIG

def conectar_banco():
    try:
        conexao = pymssql.connect(
            server=DB_CONFIG['server'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        return conexao
    except Exception as e:
        print("Erro ao conectar:", e)
        return None
