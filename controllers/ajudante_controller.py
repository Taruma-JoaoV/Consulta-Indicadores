# controllers/ajudante_controller.py
from flask import Blueprint, render_template, session, redirect, url_for, request
from models.database import conectar_banco
from datetime import date

# Cria o Blueprint
ajudante_bp = Blueprint('ajudante', __name__, url_prefix='/ajudante')

# =================== MENU ===================
@ajudante_bp.route('/menub')
def menub():
    if 'id_ajudante' not in session:
        return redirect(url_for('login.login'))
    nome = session.get('nome_ajudante', 'Usuário')
    return render_template('menub.html', nome=nome)

# =================== PAINEL ===================
@ajudante_bp.route('/painelb')
def painelb():
    if 'id_ajudante' not in session:
        return redirect(url_for('login.login'))

    id_ajudante = session['id_ajudante']
    mes_atual = date.today().strftime('%Y-%m')
    mes_selecionado = request.args.get('mes', None)

    conexao = conectar_banco()
    dados_formatados = []
    media_valor = 0
    media_meta = 0

    def calcula_media(lista):
        return round(sum(lista)/len(lista), 2) if lista else 0

    if conexao:
        cursor = conexao.cursor(as_dict=True)
        try:
            query = """
                SELECT 
                    CONVERT(varchar, Data, 23) AS DataISO,
                    ID,
                    Nome,
                    Valor,
                    Meta
                FROM Palete
                WHERE ID = %s
            """
            params = [id_ajudante]

            if mes_selecionado:
                query += " AND FORMAT(Data, 'yyyy-MM') = %s"
                params.append(mes_selecionado)

            query += " ORDER BY Data ASC"

            cursor.execute(query, tuple(params))
            resultados = cursor.fetchall()

            valores = []
            metas = []

            for linha in resultados:
                data = linha['DataISO']
                if data:
                    partes = data.split('-')
                    data_formatada = f"{partes[2]}/{partes[1]}/{partes[0]}"
                else:
                    data_formatada = "-"

                valor = linha['Valor'] if linha['Valor'] is not None else 0
                meta = linha['Meta'] if linha['Meta'] is not None else 0

                valores.append(valor)
                metas.append(meta)

                dados_formatados.append({
                    'data': data_formatada,
                    'id': linha['ID'],
                    'nome': linha['Nome'],
                    'valor': valor,
                    'meta': meta
                })

            media_valor = calcula_media(valores)
            media_meta = calcula_media(metas)

        except Exception as e:
            print("Erro ao consultar o banco:", e)
        finally:
            cursor.close()
            conexao.close()

    return render_template('painelb.html',
                           dados=dados_formatados,
                           mes_atual=mes_atual,
                           mes_selecionado=mes_selecionado,
                           media_valor=media_valor,
                           media_meta=media_meta)

# =================== 5S ===================
@ajudante_bp.route('/cinco')
def cinco():
    if 'id_ajudante' not in session:
        return redirect(url_for('login.login'))
    return render_template('cinco.html')

# =================== SONHO ===================
@ajudante_bp.route('/sonho')
def sonho():
    if 'id_ajudante' not in session:
        return redirect(url_for('login.login'))
    return render_template('sonho.html')

# =================== LOGOUT ===================
@ajudante_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.login'))
