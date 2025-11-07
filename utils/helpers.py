def calcular_media(lista, chave, ignora_percentual=False):
    valores = []
    for item in lista:
        valor = item[chave]
        if not valor or valor == "-":
            continue
        if ignora_percentual:
            valor = str(valor).replace("%", "").strip().replace(",", ".")
        try:
            valores.append(float(valor))
        except ValueError:
            continue
    if not valores:
        return "-"
    media = sum(valores) / len(valores)
    return round(media, 2)
