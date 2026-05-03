def gerar_curva_bomba(bomba):

    # 🔥 fallback inteligente
    Q_nom = (
        bomba.get("vazao_m3h")
        or bomba.get("vazao")
        or 0
    )

    H_nom = (
        bomba.get("hmt")
        or bomba.get("altura")
        or bomba.get("altura_mca")
        or 0
    )

    if Q_nom == 0 or H_nom == 0:
        return []

    pontos = []

    for fator in [0.5, 0.75, 1.0, 1.25, 1.5]:

        Q = Q_nom * fator

        # curva típica de bomba centrífuga
        H = H_nom * (1 - 0.25 * (fator - 1)**2)

        H = max(0, H)

        pontos.append({
            "vazao": Q,
            "hmt": H
        })

    return pontos