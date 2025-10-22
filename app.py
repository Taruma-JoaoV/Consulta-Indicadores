from flask import Flask, render_template, request, redirect, session, url_for
import pymssql
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'chave-padrao-fraca')

def conectar_banco():
    try:
        conn_str = os.getenv('DATABASE_URL')
        server, user, password, database = conn_str.split(';')
        conexao = pymssql.connect(
            server=server,
            user=user,
            password=password,
            database=database)
        return conexao
    except Exception as e:
        print("Erro ao conectar:", e)
        return None

@app.route('/', methods=['GET', 'POST'])
def login():
    mensagem = ''
    if request.method == 'POST':
        tipo_usuario = request.form['tipo_usuario']
        id_usuario = request.form['id_usuario']
        senha = request.form['senha']

        conexao = conectar_banco()
        if conexao:
            cursor = conexao.cursor(as_dict=True)

            if tipo_usuario == 'motorista':
                cursor.execute("SELECT * FROM Motoristas WHERE ID_Motorista = %s AND CPF = %s", (id_usuario, senha))
                usuario = cursor.fetchone()
                if usuario:
                    session['id_motorista'] = id_usuario
                    session['nome_motorista'] = usuario['Nome_Abrev'].title()

                    cursor.close()
                    conexao.close()

                    if id_usuario.upper() in ['001', '002']:
                        return redirect(url_for('painel_supervisor'))
                    else:
                        return redirect(url_for('menu'))

            elif tipo_usuario == 'ajudante':
                cursor.execute("SELECT * FROM Ajudantes WHERE ID = %s AND Senha = %s", (id_usuario, senha))
                usuario = cursor.fetchone()
                if usuario:
                    session['id_ajudante'] = id_usuario
                    session['nome_ajudante'] = usuario['Nome'].title()

                    cursor.close()
                    conexao.close()

                    if id_usuario.upper() in ['123']:
                        return redirect(url_for('painel_coordenador'))
                    else:
                        return redirect(url_for('menub'))

            cursor.close()
            conexao.close()
            mensagem = 'ID ou Senha incorretos.'

    return render_template('login.html', mensagem=mensagem)


def calcular_media(lista, chave, ignora_percentual=False):
    valores = []
    for item in lista:
        valor = item[chave]
        if not valor or valor == "-":
            continue
        if ignora_percentual:
            valor = str(valor).replace("%", "").strip().replace(",", ".")
        try:
            valor_float = float(valor)
            valores.append(valor_float)
        except ValueError:
            continue
    if not valores:
        return "-"
    media = sum(valores) / len(valores)
    return round(media, 2)


@app.route('/menu')
def menu():
    if 'id_motorista' not in session:
        return redirect(url_for('login'))

    nome = session.get('nome_motorista')
    return render_template('menu.html', nome=nome)

@app.route('/sonho')
def sonho():
    if login:
        return render_template('sonho.html')

@app.route('/cinco')
def cinco():
    if login:
        return render_template('cinco.html')

@app.route('/rota')
def rota():
    if login:
        return render_template('rota.html')

@app.route('/lups')
def lups():
    if login:
        return render_template('lups.html')
    
@app.route('/treinamentos')
def treinamentos():
    if login:
        return render_template('treinamentos.html')

@app.route('/painel')
def painel():
    if 'id_motorista' not in session:
        return redirect(url_for('login'))

    id_motorista = session['id_motorista']
    mes_selecionado = request.args.get('mes', '')

    conexao = conectar_banco()
    dados_formatados = []
    observacoes = []

    if conexao:
        cursor = conexao.cursor(as_dict=True)
        try:
            query = """
                SELECT 
                    CONVERT(varchar, D.Data, 23) AS DataISO, 
                    D.Devolucao_Porcentagem, 
                    ISNULL(S.Dispersao_KM, 0) AS Dispersao_KM,
                    R.Rating,
                    ISNULL(P.Reposicao_Valor, 0) AS Reposicao_Valor,
                    ISNULL(F.Refugo_Porcentagem, 0) AS Refugo_Porcentagem
                FROM Devolucao D
                LEFT JOIN Dispersao S ON D.ID_Motorista = S.ID_Motorista AND D.Data = S.Data
                LEFT JOIN Rating R ON D.ID_Motorista = R.ID_Motorista AND D.Data = R.Data
                LEFT JOIN Reposicao P ON D.ID_Motorista = P.ID_Motorista AND D.Data = P.Data
                LEFT JOIN Refugo F ON D.ID_Motorista = F.ID_Motorista AND D.Data = F.Data
                WHERE D.ID_Motorista = %s
            """

            params = [id_motorista]

            if mes_selecionado:
                query += " AND FORMAT(D.Data, 'yyyy-MM') = %s"
                params.append(mes_selecionado)

            query += " ORDER BY D.Data ASC"

            cursor.execute(query, tuple(params))
            resultados = cursor.fetchall()

            for linha in resultados:
                data = linha['DataISO']
                if data:
                    partes = data.split('-')
                    ano = partes[0][2:]
                    data_formatada = f"{partes[2]}/{partes[1]}/{ano}"
                else:
                    data_formatada = "-"

                devolucao_porcentagem_valor = linha['Devolucao_Porcentagem']
                if devolucao_porcentagem_valor is not None:
                    devolucao_porcentagem_valor = str(devolucao_porcentagem_valor).replace("%", "").strip()
                else:
                    devolucao_porcentagem_valor = "-"


                if devolucao_porcentagem_valor == "-" or devolucao_porcentagem_valor == "" or devolucao_porcentagem_valor is None:
                    dispersao = "-"
                    reposicao = "-"
                    refugo = "-"
                else:
                    dispersao = linha['Dispersao_KM'] if linha['Dispersao_KM'] is not None else 0
                    reposicao = linha['Reposicao_Valor'] if linha['Reposicao_Valor'] is not None else 0
                    refugo = linha['Refugo_Porcentagem'] if linha['Refugo_Porcentagem'] is not None else 0

                rating = linha['Rating'] if linha['Rating'] is not None else "-"

                dados_formatados.append({
                    'Data': data_formatada,
                    'Devolucao_Porcentagem': devolucao_porcentagem_valor,
                    'Dispersao_KM': dispersao,
                    'Rating': rating.replace(',00', ''),
                    'Reposicao_Valor': reposicao.replace('.', ','),
                    'Refugo_Porcentagem': refugo
                })

            cursor.execute("SELECT Texto FROM Observacoes WHERE ID_Motorista = %s", (id_motorista,))
            observacoes = [linha['Texto'] for linha in cursor.fetchall()]
            cursor.execute("SELECT Prontuario FROM Telemetria WHERE ID_Motorista = %s", (id_motorista,))
            resultado_prontuario = cursor.fetchone()
            prontuario = resultado_prontuario['Prontuario'] if resultado_prontuario else ""


        except Exception as e:
            print("Erro ao consultar o banco:", e)
        finally:
            cursor.close()
            conexao.close()

    media_devolucao_porcentagem = calcular_media(dados_formatados, 'Devolucao_Porcentagem', ignora_percentual=True)
    media_dispersao_km = calcular_media(dados_formatados, 'Dispersao_KM', ignora_percentual=True)
    media_rating = calcular_media(dados_formatados, 'Rating')
    soma_reposicao = sum(
        float(item['Reposicao_Valor'].replace(',', '.')) 
        for item in dados_formatados 
        if item['Reposicao_Valor'] not in (None, '', 'N/A', '-')
    )
    media_refugo = calcular_media(dados_formatados, 'Refugo_Porcentagem', ignora_percentual=True)

    return render_template('painel.html', dados=dados_formatados, observacoes=observacoes,
                           medias={
                               'Devolucao_Porcentagem': media_devolucao_porcentagem,
                               'Dispersao_KM': media_dispersao_km,
                               'Rating': media_rating,
                               'Reposicao_Valor': f"{soma_reposicao:.2f}".replace(',', '.'),
                               'Refugo_Porcentagem': media_refugo
                           },
                           prontuario=prontuario,
                           mes_atual=mes_selecionado or date.today().strftime("%Y-%m"))



@app.route('/painel_supervisor', methods=['GET', 'POST'])
def painel_supervisor():
    conexao = conectar_banco()
    funcionarios = []
    dados_formatados = []
    mensagem = ''

    # Inicializa as variáveis que serão usadas para manter estado no template
    filtro_mes = None
    id_selecionado = None

    if conexao:
        cursor = conexao.cursor(as_dict=True)

        # Busca a lista de motoristas para o select
        cursor.execute("""
            SELECT DISTINCT M.ID_Motorista, M.Nome_Completo
            FROM Motoristas M
            WHERE M.ID_Motorista IN (
                SELECT ID_Motorista FROM Devolucao
                UNION
                SELECT ID_Motorista FROM Dispersao
                UNION
                SELECT ID_Motorista FROM Rating
                UNION
                SELECT ID_Motorista FROM Reposicao
                UNION
                SELECT ID_Motorista FROM Refugo
            )
            ORDER BY M.Nome_Completo
        """)

        funcionarios = cursor.fetchall()

        if request.method == 'POST':
            id_selecionado = request.form.get('id_motorista_selecionado')
            filtro_mes = request.form.get('filtro_mes')  # Pega o mês enviado pelo form

            # Montar a query com filtro condicional para mês
            if filtro_mes:
                query = """
                    SELECT 
                        CONVERT(varchar, D.Data, 23) AS DataISO, 
                        D.Devolucao_Porcentagem, 
                        ISNULL(S.Dispersao_KM, 0) AS Dispersao_KM,
                        R.Rating,
                        ISNULL(P.Reposicao_Valor, 0) AS Reposicao_Valor,
                        ISNULL(F.Refugo_Porcentagem, 0) AS Refugo_Porcentagem
                    FROM Devolucao D
                    LEFT JOIN Dispersao S ON D.ID_Motorista = S.ID_Motorista AND D.Data = S.Data
                    LEFT JOIN Rating R ON D.ID_Motorista = R.ID_Motorista AND D.Data = R.Data
                    LEFT JOIN Reposicao P ON D.ID_Motorista = P.ID_Motorista AND D.Data = P.Data
                    LEFT JOIN Refugo F ON D.ID_Motorista = F.ID_Motorista AND D.Data = F.Data
                    WHERE D.ID_Motorista = %s AND FORMAT(D.Data, 'yyyy-MM') = %s
                    ORDER BY D.Data ASC
                """
                cursor.execute(query, (id_selecionado, filtro_mes))
            else:
                query = """
                    SELECT 
                        CONVERT(varchar, D.Data, 23) AS DataISO, 
                        D.Devolucao_Porcentagem, 
                        ISNULL(S.Dispersao_KM, 0) AS Dispersao_KM,
                        R.Rating,
                        ISNULL(P.Reposicao_Valor, 0) AS Reposicao_Valor,
                        ISNULL(F.Refugo_Porcentagem, 0) AS Refugo_Porcentagem
                    FROM Devolucao D
                    LEFT JOIN Dispersao S ON D.ID_Motorista = S.ID_Motorista AND D.Data = S.Data
                    LEFT JOIN Rating R ON D.ID_Motorista = R.ID_Motorista AND D.Data = R.Data
                    LEFT JOIN Reposicao P ON D.ID_Motorista = P.ID_Motorista AND D.Data = P.Data
                    LEFT JOIN Refugo F ON D.ID_Motorista = F.ID_Motorista AND D.Data = F.Data
                    WHERE D.ID_Motorista = %s
                    ORDER BY D.Data ASC
                """
                cursor.execute(query, (id_selecionado,))

            resultados = cursor.fetchall()

            # Processa resultados
            for linha in resultados:
                data = linha['DataISO']
                if data:
                    partes = data.split('-')
                    data_formatada = f"{partes[2]}-{partes[1]}-{partes[0]}"
                else:
                    data_formatada = "-"

                devolucao_porcentagem_valor = linha['Devolucao_Porcentagem']
                if devolucao_porcentagem_valor is None or devolucao_porcentagem_valor == "":
                    devolucao_porcentagem_valor = "-"

                if devolucao_porcentagem_valor == "-" or devolucao_porcentagem_valor == "" or devolucao_porcentagem_valor is None:
                    dispersao = "-"
                    reposicao = "-"
                    refugo = "-"
                else:
                    dispersao = linha['Dispersao_KM'] if linha['Dispersao_KM'] is not None else 0
                    reposicao = linha['Reposicao_Valor'] if linha['Reposicao_Valor'] is not None else 0
                    refugo = linha['Refugo_Porcentagem'] if linha['Refugo_Porcentagem'] is not None else 0

                rating = linha['Rating'] if linha['Rating'] is not None else "-"

                dados_formatados.append({
                    'Data': data_formatada,
                    'Devolucao_Porcentagem': devolucao_porcentagem_valor,
                    'Dispersao_KM': dispersao,
                    'Rating': rating.replace(',00', ''),
                    'Reposicao_Valor': reposicao.replace('.', ',') if isinstance(reposicao, str) else str(reposicao).replace('.', ','),
                    'Refugo_Porcentagem': refugo
                })
        cursor.execute("SELECT Prontuario FROM Telemetria WHERE ID_Motorista = %s", (id_selecionado,))
        resultado_prontuario = cursor.fetchone()
        prontuario = resultado_prontuario['Prontuario'] if resultado_prontuario else ""

        cursor.execute("SELECT Data, Texto FROM Observacoes WHERE ID_Motorista = %s", (id_selecionado,))
        observacoes = [{'data': linha['Data'], 'texto': linha['Texto']} for linha in cursor.fetchall()]

        cursor.close()
        conexao.close()

    # Calcular médias (sua função calcular_media deve estar disponível)
    media_devolucao_porcentagem = calcular_media(dados_formatados, 'Devolucao_Porcentagem', ignora_percentual=True)
    media_dispersao_km = calcular_media(dados_formatados, 'Dispersao_KM', ignora_percentual=True)
    media_rating = calcular_media(dados_formatados, 'Rating')
    soma_reposicao = sum(
        float(item['Reposicao_Valor'].replace(',', '.')) 
        for item in dados_formatados 
        if item['Reposicao_Valor'] not in (None, '', 'N/A', '-')
    )
    media_refugo = calcular_media(dados_formatados, 'Refugo_Porcentagem', ignora_percentual=True)

    medias = {
        'Devolucao_Porcentagem': media_devolucao_porcentagem,
        'Dispersao_KM': media_dispersao_km,
        'Rating': media_rating,
        'Reposicao_Valor': f"{soma_reposicao:.2f}".replace('.', ','),
        'Refugo_Porcentagem': media_refugo
    }

    return render_template(
        'painel_supervisor.html',
        funcionarios=funcionarios,
        indicadores=dados_formatados,
        mensagem=mensagem,
        medias=medias,
        filtro_mes=filtro_mes,
        id_selecionado=id_selecionado,
        prontuario=prontuario,
        observacoes=observacoes
    )


@app.route('/explicacoes')
def explicacoes():
    if 'id_motorista' not in session:
        return redirect(url_for('login'))
    return render_template('explicacoes.html')

@app.route('/observacao', methods=['POST'])
def observacao():
    if 'id_motorista' not in session:
        return redirect(url_for('login'))

    texto = request.form.get('observacao', '').strip()
    id_motorista = session['id_motorista']
    dia = datetime.now().strftime('%d/%m/%Y %H:%M')

    if texto:
        conexao = conectar_banco()
        if conexao:
            cursor = conexao.cursor(as_dict=True)
            try:
                cursor.execute("INSERT INTO Observacoes (ID_Motorista, Data, Texto) VALUES (%s, %s, %s)", (id_motorista, dia, texto))
                conexao.commit()
            except Exception as e:
                print("Erro ao salvar observação:", e)
            finally:
                cursor.close()
                conexao.close()

    return redirect(url_for('painel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#####################################################################################################
#################################   A J U D A N T E S   #############################################
#####################################################################################################
#@app.route('/loginb', methods=['GET', 'POST'])
#def loginb():
#    mensagem = ''
#    if request.method == 'POST':
#        id_ajudante = request.form['id_ajudante']
#        senha = request.form['senha']
#
#        conexao = conectar_banco()
#        if conexao:
#            cursor = conexao.cursor(as_dict=True)
#            ajudante = cursor.fetchone()
#            cursor.close()
#            conexao.close()
#
#            if ajudante:
#                session['id_ajudante'] = id_ajudante
#                session['nome_ajudante'] = ajudante['Nome'].title()
#
                # Verifica se o ID é de supervisor
#                if id_ajudante.upper() in ['123']:
#                    return redirect(url_for('painel_coordenador'))
#                else:
#                    return redirect(url_for('menub'))
#
#            else:
#                mensagem = 'ID ou Senha incorretos.'
#
#    return render_template('loginb.html', mensagem=mensagem)
#
@app.route('/menub')
def menub():
    if 'id_ajudante' not in session:
        return redirect(url_for('loginb'))

    nome = session.get('nome_ajudante')
    return render_template('menub.html', nome=nome)

@app.route('/painelb')
def painelb():
    if 'id_ajudante' not in session:
        return redirect(url_for('login'))

    id_ajudante = session['id_ajudante']
    mes_selecionado = request.args.get('mes', '')

    conexao = conectar_banco()
    dados_formatados = []
    media_valor = 0
    media_meta = 0

    def calcula_media(lista):
        if lista:
            return round(sum(lista) / len(lista), 2)
        return 0

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

                valor = linha['Valor']
                meta = linha['Meta']

                if valor is not None:
                    valores.append(valor)
                if meta is not None:
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
                           mes_selecionado=mes_selecionado,
                           media_valor=media_valor,
                           media_meta=media_meta)

@app.route('/painel_coordenador')
def painel_coordenador():
    if 'id_ajudante' not in session:
        return redirect(url_for('loginb'))

    mes_selecionado = request.args.get('mes', '')
    ajudante_selecionado = request.args.get('ajudante', '')

    conexao = conectar_banco()
    dados_formatados = []
    media_valor = 0
    media_meta = 0
    lista_ajudantes = []

    def calcula_media(lista):
        if lista:
            return round(sum(lista) / len(lista), 2)
        return 0

    if conexao:
        cursor = conexao.cursor(as_dict=True)
        try:

            cursor.execute("SELECT DISTINCT Nome FROM Ajudantes WHERE Nome <> 'Coordenador João' ORDER BY Nome ASC")
            lista_ajudantes = [row['Nome'] for row in cursor.fetchall()]

            # Carrega dados da tabela Palete
            query = """
                SELECT 
                    CONVERT(varchar, Data, 23) AS DataISO,
                    ID,
                    Nome,
                    Valor,
                    Meta
                FROM Palete
                WHERE 1=1
            """
            params = []

            if ajudante_selecionado:
                query = """
                    SELECT 
                        CONVERT(varchar, Data, 23) AS DataISO,
                        ID,
                        Nome,
                        Valor,
                        Meta
                    FROM Palete
                    WHERE Nome = %s
                """
                params = [ajudante_selecionado]

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

                valor = linha['Valor']
                meta = linha['Meta']

                if valor is not None:
                    valores.append(valor)
                if meta is not None:
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
            print("Erro ao consultar o banco (coordenador):", e)
        finally:
            cursor.close()
            conexao.close()

    return render_template('painel_coordenador.html',
                           dados=dados_formatados,
                           mes_selecionado=mes_selecionado,
                           ajudante_selecionado=ajudante_selecionado,
                           lista_ajudantes=lista_ajudantes,
                           media_valor=media_valor,
                           media_meta=media_meta)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
