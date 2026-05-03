"""
catalogo_bocais.py
==================
Catálogo real de bocais para pivô central.

Fonte: Senninger i-WOB2 — brochure oficial 2019
       agriculture.hunterirrigation.com

k e x calculados por regressão log-log em 3 pontos de pressão:
  6 psi (4.22 mca), 10 psi (7.03 mca), 15 psi (10.54 mca)
Erro médio da regressão: 0.056% — praticamente exato.

Equação: q [m³/h] = k × P [mca]^x

Modelos disponíveis (deflectores):
  "cinza"   — Ângulo padrão, 6 ranhuras, gotas pequenas  (argilas)
  "preto"   — Ângulo padrão, 9 ranhuras, gotas médias    (silte/franco)
  "azul"    — Ângulo baixo,  9 ranhuras, gotas médias    (silte/franco)
  "branco"  — Ângulo baixo,  6 ranhuras, gotas grandes   (arenosos)

Faixas de bocal por modelo e pressão:
  cinza  @ 0.41 bar: #12–26 | @ 0.69–1.03 bar: #10–26
  preto  @ 0.41 bar: #12–26 | @ 0.69–1.03 bar: #6–26
  azul   @ 0.41 bar: #12–26 | @ 0.69–1.03 bar: #6–26
  branco @ 0.41 bar: #12–26 | @ 0.69–1.03 bar: #12–26
"""

# Pressões de referência em mca (1 psi = 0.703 mca)
P_MIN_MCA   = 4.22    # 6 psi
P_IDEAL_MCA = 7.03    # 10 psi
P_MAX_MCA   = 10.54   # 15 psi

# Espaçamento máximo por pressão (todos os modelos)
ESPAC_MAX_P_MIN_M   = 3.0   # @ 0.41 bar
ESPAC_MAX_P_IDEAL_M = {      # @ 0.69–1.03 bar (varia por modelo)
    "cinza":  5.5,
    "preto":  6.1,
    "azul":   5.5,
    "branco": 4.6,
}

# Bocal mínimo por modelo e faixa de pressão
BOCAL_MIN = {
    "cinza":  {"p_min": 12, "p_ideal": 10},
    "preto":  {"p_min": 12, "p_ideal":  6},
    "azul":   {"p_min": 12, "p_ideal":  6},
    "branco": {"p_min": 12, "p_ideal": 12},
}

# Catálogo completo: 41 bocais — #6 a #26 (inteiros e meios)
# Campos: numero, cor, orificio_mm, k_m3h, x
# q [m³/h] = k × P [mca]^x
BOCAIS = [
    {"numero": 6,    "cor": "Gold",           "orificio_mm": 2.38,  "k_m3h": 0.068619, "x": 0.5003},
    {"numero": 6.5,  "cor": "—",              "orificio_mm": 2.59,  "k_m3h": 0.080912, "x": 0.5003},
    {"numero": 7,    "cor": "Lime",           "orificio_mm": 2.78,  "k_m3h": 0.094025, "x": 0.5003},
    {"numero": 7.5,  "cor": "—",              "orificio_mm": 2.97,  "k_m3h": 0.107137, "x": 0.5003},
    {"numero": 8,    "cor": "Lavender",       "orificio_mm": 3.18,  "k_m3h": 0.122795, "x": 0.5009},
    {"numero": 8.5,  "cor": "—",              "orificio_mm": 3.38,  "k_m3h": 0.138453, "x": 0.5006},
    {"numero": 9,    "cor": "Grey",           "orificio_mm": 3.57,  "k_m3h": 0.155073, "x": 0.5009},
    {"numero": 9.5,  "cor": "—",              "orificio_mm": 3.76,  "k_m3h": 0.173887, "x": 0.5005},
    {"numero": 10,   "cor": "Turquoise",      "orificio_mm": 3.97,  "k_m3h": 0.192040, "x": 0.5006},
    {"numero": 10.5, "cor": "—",              "orificio_mm": 4.17,  "k_m3h": 0.212165, "x": 0.5006},
    {"numero": 11,   "cor": "Yellow",         "orificio_mm": 4.37,  "k_m3h": 0.232290, "x": 0.5006},
    {"numero": 11.5, "cor": "—",              "orificio_mm": 4.57,  "k_m3h": 0.254388, "x": 0.5009},
    {"numero": 12,   "cor": "Red",            "orificio_mm": 4.76,  "k_m3h": 0.277161, "x": 0.5009},
    {"numero": 12.5, "cor": "—",              "orificio_mm": 4.95,  "k_m3h": 0.300909, "x": 0.5009},
    {"numero": 13,   "cor": "White",          "orificio_mm": 5.16,  "k_m3h": 0.326618, "x": 0.5009},
    {"numero": 13.5, "cor": "—",              "orificio_mm": 5.36,  "k_m3h": 0.351839, "x": 0.5005},
    {"numero": 14,   "cor": "Blue",           "orificio_mm": 5.56,  "k_m3h": 0.378148, "x": 0.5005},
    {"numero": 14.5, "cor": "—",              "orificio_mm": 5.77,  "k_m3h": 0.406427, "x": 0.5003},
    {"numero": 15,   "cor": "Dk. Brown",      "orificio_mm": 5.95,  "k_m3h": 0.434705, "x": 0.5003},
    {"numero": 15.5, "cor": "—",              "orificio_mm": 6.15,  "k_m3h": 0.464453, "x": 0.5003},
    {"numero": 16,   "cor": "Orange",         "orificio_mm": 6.35,  "k_m3h": 0.496410, "x": 0.4989},
    {"numero": 16.5, "cor": "—",              "orificio_mm": 6.55,  "k_m3h": 0.527393, "x": 0.4996},
    {"numero": 17,   "cor": "Dk. Green",      "orificio_mm": 6.75,  "k_m3h": 0.560345, "x": 0.4996},
    {"numero": 17.5, "cor": "—",              "orificio_mm": 6.93,  "k_m3h": 0.593297, "x": 0.4996},
    {"numero": 18,   "cor": "Purple",         "orificio_mm": 7.14,  "k_m3h": 0.627920, "x": 0.4992},
    {"numero": 18.5, "cor": "—",              "orificio_mm": 7.34,  "k_m3h": 0.663512, "x": 0.4996},
    {"numero": 19,   "cor": "Black",          "orificio_mm": 7.54,  "k_m3h": 0.699104, "x": 0.4996},
    {"numero": 19.5, "cor": "—",              "orificio_mm": 7.75,  "k_m3h": 0.736165, "x": 0.4996},
    {"numero": 20,   "cor": "Dk. Turquoise",  "orificio_mm": 7.94,  "k_m3h": 0.773573, "x": 0.4996},
    {"numero": 20.5, "cor": "—",              "orificio_mm": 8.13,  "k_m3h": 0.811461, "x": 0.4996},
    {"numero": 21,   "cor": "Mustard",        "orificio_mm": 8.33,  "k_m3h": 0.851781, "x": 0.4996},
    {"numero": 21.5, "cor": "—",              "orificio_mm": 8.53,  "k_m3h": 0.891574, "x": 0.5000},
    {"numero": 22,   "cor": "Maroon",         "orificio_mm": 8.73,  "k_m3h": 0.932290, "x": 0.5000},
    {"numero": 22.5, "cor": "—",              "orificio_mm": 8.94,  "k_m3h": 0.973981, "x": 0.5000},
    {"numero": 23,   "cor": "Cream",          "orificio_mm": 9.13,  "k_m3h": 1.016157, "x": 0.5000},
    {"numero": 23.5, "cor": "—",              "orificio_mm": 9.32,  "k_m3h": 1.059808, "x": 0.5000},
    {"numero": 24,   "cor": "Dk. Blue",       "orificio_mm": 9.53,  "k_m3h": 1.103940, "x": 0.4998},
    {"numero": 24.5, "cor": "—",              "orificio_mm": 9.73,  "k_m3h": 1.148558, "x": 0.4998},
    {"numero": 25,   "cor": "Copper",         "orificio_mm": 9.92,  "k_m3h": 1.193175, "x": 0.5002},
    {"numero": 25.5, "cor": "—",              "orificio_mm": 10.11, "k_m3h": 1.239754, "x": 0.5002},
    {"numero": 26,   "cor": "Bronze",         "orificio_mm": 10.32, "k_m3h": 1.282147, "x": 0.5004},
]


def vazao_bocal_m3h(numero_bocal: float, P_mca: float) -> float:
    """Retorna a vazão do bocal em m³/h dado P em mca."""
    bocal = obter_bocal(numero_bocal)
    if not bocal or P_mca <= 0:
        return 0.0
    return bocal["k_m3h"] * (P_mca ** bocal["x"])


def obter_bocal(numero: float) -> dict:
    """Retorna o dict do bocal pelo número (ex: 14, 14.5)."""
    for b in BOCAIS:
        if abs(b["numero"] - numero) < 0.01:
            return b
    return None


def selecionar_bocal(
    q_necessaria_m3h: float,
    P_disponivel_mca: float,
    modelo_deflector: str = "preto",
    P_projeto_mca: float = None,
) -> dict:
    """
    Seleciona o bocal adequado para entregar q_necessaria com P_disponivel.

    Parâmetros
    ----------
    q_necessaria_m3h  : vazão que o bocal precisa entregar (m³/h)
    P_disponivel_mca  : pressão disponível no ponto (mca)
    modelo_deflector  : "cinza" | "preto" | "azul" | "branco"
    P_projeto_mca     : pressão de projeto (se None, usa P_disponivel)

    Retorna
    -------
    dict com: numero, cor, orificio_mm, k_m3h, x,
              q_calculada_m3h, q_calculada_l_h,
              P_necessaria_mca, dentro_da_faixa
    """
    if P_disponivel_mca <= 0 or q_necessaria_m3h <= 0:
        return None

    P_ref = P_projeto_mca or P_disponivel_mca

    # bocal mínimo permitido para o modelo e pressão
    bocal_min = BOCAL_MIN.get(modelo_deflector, {})
    num_min = bocal_min.get("p_ideal", 12) if P_ref >= P_IDEAL_MCA else bocal_min.get("p_min", 12)

    melhor = None
    menor_erro = float("inf")

    for b in BOCAIS:
        if b["numero"] < num_min:
            continue
        q_calc = b["k_m3h"] * (P_disponivel_mca ** b["x"])
        erro = abs(q_calc - q_necessaria_m3h)
        if erro < menor_erro:
            menor_erro = erro
            melhor = b

    if melhor is None:
        return None

    q_calc = melhor["k_m3h"] * (P_disponivel_mca ** melhor["x"])
    # P necessária para entregar exatamente q_necessaria
    P_nec = (q_necessaria_m3h / melhor["k_m3h"]) ** (1.0 / melhor["x"])

    return {
        "numero":           melhor["numero"],
        "cor":              melhor["cor"],
        "orificio_mm":      melhor["orificio_mm"],
        "k_m3h":            melhor["k_m3h"],
        "x":                melhor["x"],
        "modelo_deflector": modelo_deflector,
        "q_calculada_m3h":  round(q_calc, 5),
        "q_calculada_l_h":  round(q_calc * 1000, 2),
        "P_necessaria_mca": round(P_nec, 2),
        "P_disponivel_mca": round(P_disponivel_mca, 2),
        "dentro_da_faixa":  P_MIN_MCA <= P_disponivel_mca <= P_MAX_MCA,
        "desvio_q_pct":     round((q_calc - q_necessaria_m3h) / q_necessaria_m3h * 100, 2)
                            if q_necessaria_m3h > 0 else 0,
    }
