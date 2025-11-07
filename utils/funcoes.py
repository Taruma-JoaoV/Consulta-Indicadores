def formatar_dados(resultados):
    """
    Recebe uma lista de tuplas ou dicionários retornados do banco
    e converte em uma lista de dicionários com chaves padronizadas.
    """
    dados_formatados = []

    for item in resultados:
        # Garante que o item seja um dicionário
        if not isinstance(item, dict):
            continue

        dados_formatados.append({
            'Data': item.get('Data'),
            'Devolucao_Porcentagem': item.get('Devolucao_Porcentagem'),
            'Refugo_Porcentagem': item.get('Refugo_Porcentagem'),
            'Reposicao_Valor': item.get('Reposicao_Valor'),
            'Rating': item.get('Rating'),
            'Dispersao_KM': item.get('Dispersao_KM')
        })

    return dados_formatados


def calcular_media(lista, chave, ignora_percentual=False):
    """
    Calcula a média de valores em uma lista de dicionários.

    Args:
        lista (list): Lista de dicionários contendo os dados.
        chave (str): Chave cujo valor será usado para cálculo.
        ignora_percentual (bool): Se True, remove '%' antes de converter.

    Returns:
        float ou str: Média arredondada para 2 casas ou '-' se não houver valores válidos.
    """
    valores_validos = []

    for item in lista:
        valor = item.get(chave, None)

        if valor is None or valor == '' or valor == '-':
            continue

        if isinstance(valor, str):
            # Remove percentual se necessário
            if ignora_percentual and '%' in valor:
                valor = valor.replace('%', '')
            # Substitui vírgula por ponto
            valor = valor.replace(',', '.').strip()

        try:
            num = float(valor)
            valores_validos.append(num)
        except (ValueError, TypeError):
            continue

    if not valores_validos:
        return '-'

    media = sum(valores_validos) / len(valores_validos)
    return round(media, 2)



def calcular_medias_gerais(dados):
    """
    Gera um dicionário com todas as médias consolidadas.
    """
    return {
        'Devolucao_Porcentagem': calcular_media(dados, 'Devolucao_Porcentagem', ignora_percentual=True),
        'Refugo_Porcentagem': calcular_media(dados, 'Refugo_Porcentagem', ignora_percentual=True),
        'Reposicao_Valor': calcular_media(dados, 'Reposicao_Valor'),
        'Rating': calcular_media(dados, 'Rating'),
        'Dispersao_KM': calcular_media(dados, 'Dispersao_KM', ignora_percentual=True)
    }
