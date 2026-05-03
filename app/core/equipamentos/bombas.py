import bisect

# --------------------------------------------------
# BASE DE DADOS (EXPANSÍVEL)
# --------------------------------------------------

BOMBAS = [
{
"modelo": "KSB-100-200",
"curva": [
{"q": 50, "h": 80, "eta": 0.70},
{"q": 80, "h": 75, "eta": 0.75},
{"q": 100, "h": 70, "eta": 0.78},
{"q": 120, "h": 60, "eta": 0.74},
]
},
{
"modelo": "SCHNEIDER-BC92",
"curva": [
{"q": 40, "h": 60, "eta": 0.68},
{"q": 70, "h": 55, "eta": 0.72},
{"q": 90, "h": 50, "eta": 0.75},
]
}
]

# --------------------------------------------------
# INTERPOLAÇÃO
# --------------------------------------------------

def interpolar_curva(curva, vazao):


    curva_ordenada = sorted(curva, key=lambda x: x["q"])
    qs = [p["q"] for p in curva_ordenada]

    if vazao < qs[0] or vazao > qs[-1]:
        return None  # fora da faixa

    i = bisect.bisect_left(qs, vazao)

    if qs[i] == vazao:
        return curva_ordenada[i]

    p1 = curva_ordenada[i - 1]
    p2 = curva_ordenada[i]

    frac = (vazao - p1["q"]) / (p2["q"] - p1["q"])

    h = p1["h"] + frac * (p2["h"] - p1["h"])
    eta = p1["eta"] + frac * (p2["eta"] - p1["eta"])

    return {
        "q": vazao,
        "h": round(h, 2),
        "eta": round(eta, 3)
    }

# --------------------------------------------------
# SELEÇÃO PROFISSIONAL
# --------------------------------------------------

def selecionar_bomba(vazao_m3h, hmt_requerido):


    candidatas = []

    for bomba in BOMBAS:

        ponto = interpolar_curva(bomba["curva"], vazao_m3h)

        if not ponto:
            continue  # fora da faixa

        h_bomba = ponto["h"]
        margem = h_bomba - hmt_requerido

        if margem >= 0:
            candidatas.append({
                "modelo": bomba["modelo"],
                "vazao_m3h": vazao_m3h,
                "altura_m": h_bomba,
                "eficiencia": ponto["eta"],
                "margem_m": round(margem, 2)
            })

    # -----------------------------------------
    # NENHUMA BOMBA ATENDE
    # -----------------------------------------
    if not candidatas:
        return None

    # -----------------------------------------
    # ESCOLHER MELHOR (menor sobra + melhor eficiência)
    # -----------------------------------------
    candidatas.sort(key=lambda x: (x["margem_m"], -x["eficiencia"]))

    return candidatas[0]

