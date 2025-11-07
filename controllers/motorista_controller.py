from flask import Blueprint, render_template, request, redirect, session, url_for
from models.database import conectar_banco
from utils.funcoes import calcular_media
from datetime import date

motorista_bp = Blueprint('motorista', __name__, url_prefix='/motorista')

# ---------- MENU ----------
@motorista_bp.route('/menu')
def menu():
    if 'id_motorista' not in session:
        return redirect(url_for('login.login'))
    nome = session.get('nome_motorista')
    return render_template('menu.html', nome=nome)


# ---------- PAINEL ----------
@motorista_bp.route('/painel')
def painel():
    if 'id_motorista' not in session:
        return redirect(url_for('login.login'))

    id_motorista = session['id_motorista']
    mes_selecionado = request.args.get('mes', '')
    conexao = conectar_banco()
    dados_formatados = []
    observacoes = []
    prontuario = ''
    gsd = ''

    if conexao:
        cursor = conexao.cursor(as_dict=True)
        try:
            query = """
                SELECT CONVERT(varchar, D.Data, 23) AS DataISO,
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

                devolucao_valor = linha['Devolucao_Porcentagem']
                if devolucao_valor is not None:
                    devolucao_valor = str(devolucao_valor).replace("%", "").strip()
                else:
                    devolucao_valor = "-"

                if devolucao_valor in ("-", "", None):
                    dispersao = reposicao = refugo = "-"
                else:
                    dispersao = linha['Dispersao_KM'] or 0
                    reposicao = linha['Reposicao_Valor'] or 0
                    refugo = linha['Refugo_Porcentagem'] or 0

                rating = linha['Rating'] if linha['Rating'] is not None else "-"

                dados_formatados.append({
                    'Data': data_formatada,
                    'Devolucao_Porcentagem': devolucao_valor,
                    'Dispersao_KM': dispersao,
                    'Rating': rating.replace(',00', '') if isinstance(rating, str) else rating,
                    'Reposicao_Valor': str(reposicao).replace('.', ',') if isinstance(reposicao, (int, float)) else reposicao,
                    'Refugo_Porcentagem': refugo
                })

            # Observações
            cursor.execute("SELECT Data, Texto FROM Observacoes WHERE ID_Motorista = %s", (id_motorista,))
            observacoes = [{'data': linha['Data'], 'texto': linha['Texto']} for linha in cursor.fetchall()]

            # Telemetria
            cursor.execute("SELECT Prontuario FROM Telemetria WHERE ID_Motorista = %s", (id_motorista,))
            resultado_prontuario = cursor.fetchone()
            prontuario = resultado_prontuario['Prontuario'] if resultado_prontuario else ""

            # GSD
            cursor.execute("SELECT Data FROM GSD WHERE ID_Motorista = %s", (id_motorista,))
            data_gsd = cursor.fetchone()
            gsd = data_gsd['Data'] if data_gsd else ""

        except Exception as e:
            print("Erro ao consultar o banco:", e)
        finally:
            cursor.close()
            conexao.close()

    # Cálculo de médias
    media_devolucao_porcentagem = calcular_media(dados_formatados, 'Devolucao_Porcentagem', ignora_percentual=True)
    media_dispersao_km = calcular_media(dados_formatados, 'Dispersao_KM', ignora_percentual=True)
    media_rating = calcular_media(dados_formatados, 'Rating')
    soma_reposicao = sum(
        float(item['Reposicao_Valor'].replace(',', '.'))
        for item in dados_formatados
        if item['Reposicao_Valor'] not in (None, '', 'N/A', '-')
    )
    media_refugo = calcular_media(dados_formatados, 'Refugo_Porcentagem', ignora_percentual=True)

    return render_template('painel.html',
                           dados=dados_formatados,
                           observacoes=observacoes,
                           medias={
                               'Devolucao_Porcentagem': media_devolucao_porcentagem,
                               'Dispersao_KM': media_dispersao_km,
                               'Rating': media_rating,
                               'Reposicao_Valor': f"{soma_reposicao:.2f}".replace('.', ','),
                               'Refugo_Porcentagem': media_refugo
                           },
                           prontuario=prontuario,
                           gsd=gsd,
                           mes_atual=mes_selecionado or date.today().strftime("%Y-%m")
                           )


# ---------- LOGOUT ----------
@motorista_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login.login'))


# ---------- OBSERVAÇÃO ----------
@motorista_bp.route('/observacao', methods=['POST'])
def observacao():
    if 'id_motorista' not in session:
        return redirect(url_for('login.login'))

    id_motorista = session['id_motorista']
    texto = request.form.get('observacao', '').strip()

    if texto:
        conexao = conectar_banco()
        if conexao:
            cursor = conexao.cursor()
            try:
                cursor.execute("INSERT INTO Observacoes (ID_Motorista, Texto, Data) VALUES (%s, %s, GETDATE())",
                               (id_motorista, texto))
                conexao.commit()
            except Exception as e:
                print("Erro ao inserir observação:", e)
            finally:
                cursor.close()
                conexao.close()

    return redirect(url_for('motorista.painel'))


# ---------- ROTAS SECUNDÁRIAS DO MENU ----------
@motorista_bp.route('/sonho')
def sonho():
    if 'id_motorista' not in session:
        return redirect(url_for('login.login'))
    return render_template('sonho.html')


@motorista_bp.route('/cinco')
def cinco():
    if 'id_motorista' not in session:
        return redirect(url_for('login.login'))
    return render_template('cinco.html')


@motorista_bp.route('/rota')
def rota():
    if 'id_motorista' not in session:
        return redirect(url_for('login.login'))
    return render_template('rota.html')


@motorista_bp.route('/lups')
def lups():
    if 'id_motorista' not in session:
        return redirect(url_for('login.login'))
    return render_template('lups.html')


@motorista_bp.route('/treinamentos')
def treinamentos():
    if 'id_motorista' not in session:
        return redirect(url_for('login.login'))
    return render_template('treinamentos.html')


@motorista_bp.route('/explicacoes')
def explicacoes():
    if 'id_motorista' not in session:
        return redirect(url_for('login.login'))
    return render_template('explicacoes.html')
