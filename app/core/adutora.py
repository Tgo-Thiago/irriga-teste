import math
from core.hydraulics import perda_darcy
from core.perdas_localizadas import calcular_perdas_localizadas

# ---------------------------------------------

# DIÂMETROS COMERCIAIS

# ---------------------------------------------

DIAMETROS_COMERCIAIS = [
{"nome": "100 mm", "m": 0.1},
{"nome": "150 mm", "m": 0.15},
{"nome": "200 mm", "m": 0.2},
{"nome": "250 mm", "m": 0.25},
{"nome": "300 mm", "m": 0.3},
]

# ---------------------------------------------

# ESCOLHA DE DIÂMETRO (MELHORADA)

# ---------------------------------------------

def escolher_diametro_adutora(vazao_m3h):


    Q = vazao_m3h / 3600
    velocidade_alvo = 1.5

    melhor = None
    menor_erro = float("inf")

    for d in DIAMETROS_COMERCIAIS:

        A = math.pi * (d["m"] / 2) ** 2
        v = Q / A if A > 0 else 0

        # elimina velocidade muito baixa
        if v < 0.8:
            continue

        # elimina velocidade muito alta
        if v > 2.5:
            continue

        erro = abs(v - velocidade_alvo)

        if erro < menor_erro:
            menor_erro = erro
            melhor = d

    # fallback → menor diâmetro que não ultrapasse velocidade crítica
    if not melhor:
        for d in DIAMETROS_COMERCIAIS:
            A = math.pi * (d["m"] / 2) ** 2
            v = Q / A if A > 0 else 0

            if v <= 2.5:
                return d

    return melhor if melhor else DIAMETROS_COMERCIAIS[-1]

# ---------------------------------------------

# CÁLCULO DA ADUTORA (COM PERDAS LOCALIZADAS)

# ---------------------------------------------

def calcular_adutora(vazao_m3h, segmentos):


    Q = vazao_m3h / 3600

    perda_total = 0
    detalhes = []

    rugosidades = {
        "PVC": 0.0000015,
        "PEAD": 0.00001,
        "ACO": 0.000045
    }

    for seg in segmentos:

        D = seg["diametro_interno_m"]
        L = seg["comprimento_m"]
        material = seg.get("material", "PVC")
        componentes = seg.get("componentes", [])

        # -----------------------------------------
        # ÁREA E VELOCIDADE
        # -----------------------------------------
        A = math.pi * (D / 2) ** 2
        v = Q / A if A > 0 else 0

     # -----------------------------------------
     # RUGOSIDADE
     # -----------------------------------------
        rugosidade = rugosidades.get(material, 0.000045)

        # -----------------------------------------
        # PERDA DISTRIBUÍDA (DARCY)
        # -----------------------------------------
        hf_dist, f, _ = perda_darcy(L, D, v, rugosidade)

        # -----------------------------------------
        # PERDAS LOCALIZADAS (NOVO)
        # -----------------------------------------
        hf_local, K_total = calcular_perdas_localizadas(v, componentes)

        # -----------------------------------------
        # SOMA TOTAL DO TRECHO
        # -----------------------------------------
        hf_total = hf_dist + hf_local
        perda_total += hf_total

        # -----------------------------------------
        # DETALHAMENTO
        # -----------------------------------------
        detalhes.append({
            "comprimento_m": L,
            "diametro_m": D,
            "material": material,
            "velocidade_m_s": round(v, 3),
            "fator_atrito": round(f, 4),
            "perda_distribuida_mca": round(hf_dist, 3),
            "perda_localizada_mca": round(hf_local, 3),
            "k_total": K_total,
            "perda_total_mca": round(hf_total, 3),
            "componentes": componentes
        })

    # ---------------------------------------------
    # VELOCIDADE MÉDIA
    # ---------------------------------------------
        velocidade_media = (
            sum(d["velocidade_m_s"] for d in detalhes) / len(detalhes)
            if detalhes else 0
        )

    return {
     "perda_total_mca": round(perda_total, 3),
        "velocidade_media_m_s": round(velocidade_media, 3),
        "segmentos": detalhes
    }

