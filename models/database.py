# models/database.py
import os
import pymssql


def conectar_banco():
    """
    Conecta ao banco de dados usando:
    - DATABASE_URL do ambiente (produção)
    - ou DB_CONFIG do config.py (desenvolvimento local)
    
    DATABASE_URL esperado: server;user;password;database
    """
    try:
        conn_str = os.getenv('DATABASE_URL')
        if conn_str:
            # Divide a string em partes
            parts = conn_str.split(';')
            if len(parts) != 4:
                raise ValueError("DATABASE_URL inválida. Deve conter server;user;password;database")
            server, user, password, database = parts
        else:
            # Usa configuração local
            server = DB_CONFIG['server']
            user = DB_CONFIG['user']
            password = DB_CONFIG['password']
            database = DB_CONFIG['database']

        conexao = pymssql.connect(
            server=server,
            user=user,
            password=password,
            database=database
        )
        return conexao

    except Exception as e:
        print("Erro ao conectar:", e)
        return None
