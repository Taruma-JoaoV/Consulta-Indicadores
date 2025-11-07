from flask import Blueprint, render_template, redirect, session, request, url_for
from models.database import conectar_banco
from utils.helpers import calcular_media

supervisor_bp = Blueprint('supervisor', __name__)

@supervisor_bp.route('/painel_supervisor', methods=['GET', 'POST'])
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

        cursor.execute("SELECT Data FROM GSD WHERE ID_Motorista = %s", (id_selecionado,))
        data_gsd = cursor.fetchone()
        gsd = data_gsd['Data'] if data_gsd else ""

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
        gsd=gsd,
        observacoes=observacoes
    )

@supervisor_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.login'))


@supervisor_bp.route('/painel_coordenador')
def painel_coordenador():
    if 'id_ajudante' not in session:
        return redirect(url_for('login.login'))

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
