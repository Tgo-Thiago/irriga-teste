import math

# --------------------------------------------------
# CATÁLOGO DE EMISSORES
# k em m³/h (coeficiente do bocal/aspersor)
# --------------------------------------------------
EMISSORES = [
    {
        "modelo": "Padrao",
        "pressao_min": 10,
        "pressao_max": 35,
        "k": 0.12,   # m³/h
        "x": 0.5,
    }
]


def selecionar_emissor(pressao_media):
    for e in EMISSORES:
        if e["pressao_min"] <= pressao_media <= e["pressao_max"]:
            return e
    return EMISSORES[0]


# --------------------------------------------------
# VAZÃO PONTUAL DE UM EMISSOR
# retorna m³/s
# --------------------------------------------------
def calcular_vazao_emissor_pressao(k_m3h, x, pressao_mca):
    """
    q = k * P^x   [m³/h]  → divide por 3600 → m³/s
    BUG CORRIGIDO: antes dividia por 3600 duas vezes
    (uma vez aqui e outra no construtor Emissor).
    """
    if pressao_mca <= 0:
        return 0.0
    return (k_m3h * (pressao_mca ** x)) / 3600.0


# --------------------------------------------------
# GERAÇÃO DE EMISSORES A PARTIR DO PERFIL DE PRESSÃO
# --------------------------------------------------
def gerar_emissores(perfil_pivo, espacamento_m, vazao_total_m3h=None):
    """
    BUG CORRIGIDO:
    1. pressao buscada no perfil usava comparação '>= r' — pode pular pontos.
       Agora usa interpolação linear entre os dois pontos mais próximos.
    2. 'vazao_media_l_h' e 'pressao_media_mca' não eram calculados,
       mas o PDF tentava lê-los → campos adicionados no resultado.
    3. 'vazao_l_h' não era calculado — adicionado por emissor para o PDF.
    """
    if not perfil_pivo:
        return _resultado_vazio(espacamento_m)

    R_total = perfil_pivo[-1]["posicao_m"]

    # posições dos emissores ao longo do raio
    posicoes = []
    r = espacamento_m
    while r <= R_total:
        posicoes.append(round(r, 2))
        r += espacamento_m

    if not posicoes:
        return _resultado_vazio(espacamento_m)

    # emissor de referência baseado na pressão média do perfil
    pressao_media_perfil = sum(p["pressao_mca"] for p in perfil_pivo) / len(perfil_pivo)
    emissor_ref = selecionar_emissor(pressao_media_perfil)
    k = emissor_ref["k"]
    x = emissor_ref["x"]

    emissores = []
    for r in posicoes:
        pressao = _interpolar_pressao(perfil_pivo, r)
        pressao = max(pressao, 0.1)

        q_m3s = calcular_vazao_emissor_pressao(k, x, pressao)
        q_m3h = q_m3s * 3600.0
        q_lh  = q_m3h * 1000.0

        emissores.append({
            "posicao_m":    r,
            "pressao_mca":  round(pressao, 2),
            "vazao_m3s":    round(q_m3s, 7),
            "vazao_m3h":    round(q_m3h, 5),
            "vazao_l_h":    round(q_lh, 2),      # ← para o PDF
            "modelo":       emissor_ref["modelo"],
        })

    vazao_total_calc = sum(e["vazao_m3h"] for e in emissores)
    pressao_media    = sum(e["pressao_mca"] for e in emissores) / len(emissores) if emissores else 0
    vazao_media_lh   = sum(e["vazao_l_h"] for e in emissores) / len(emissores) if emissores else 0

    return {
        "emissores":                   emissores,
        "quantidade":                  len(emissores),
        "espacamento_m":               espacamento_m,
        "vazao_total_calculada_m3h":   round(vazao_total_calc, 3),
        "vazao_media_l_h":             round(vazao_media_lh, 2),   # ← para o PDF
        "pressao_media_mca":           round(pressao_media, 2),    # ← para o PDF
        "modelo_emissor":              emissor_ref["modelo"],
    }


# --------------------------------------------------
# INTERPOLAÇÃO LINEAR DE PRESSÃO NO PERFIL
# --------------------------------------------------
def _interpolar_pressao(perfil, r):
    """Interpola linearmente a pressão entre os dois pontos do perfil mais próximos de r."""
    if r <= perfil[0]["posicao_m"]:
        return perfil[0]["pressao_mca"]
    if r >= perfil[-1]["posicao_m"]:
        return perfil[-1]["pressao_mca"]

    for i in range(len(perfil) - 1):
        p1 = perfil[i]
        p2 = perfil[i + 1]
        if p1["posicao_m"] <= r <= p2["posicao_m"]:
            span = p2["posicao_m"] - p1["posicao_m"]
            if span == 0:
                return p1["pressao_mca"]
            frac = (r - p1["posicao_m"]) / span
            return p1["pressao_mca"] + frac * (p2["pressao_mca"] - p1["pressao_mca"])

    return perfil[-1]["pressao_mca"]


def _resultado_vazio(espacamento_m):
    return {
        "emissores": [],
        "quantidade": 0,
        "espacamento_m": espacamento_m,
        "vazao_total_calculada_m3h": 0.0,
        "vazao_media_l_h": 0.0,
        "pressao_media_mca": 0.0,
        "modelo_emissor": "N/A",
    }
