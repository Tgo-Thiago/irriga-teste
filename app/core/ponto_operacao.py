def encontrar_ponto_operacao(curva_sistema, curva_bomba):

    melhor = None
    menor_erro = float("inf")

    for s in curva_sistema:
        for b in curva_bomba:

            erro = abs(s["hmt"] - b["hmt"])

            if erro < menor_erro:
                menor_erro = erro
                melhor = {
                    "vazao": s["vazao"],
                    "hmt": (s["hmt"] + b["hmt"]) / 2,
                    "erro": erro
                }

    return melhor