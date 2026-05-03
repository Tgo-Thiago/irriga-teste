"""
modulo_agronomico.py
====================
Módulo agronômico para dimensionamento de pivô central.
Calcula lâmina bruta, turno de rega e verificação de taxa de aplicação.

Fontes:
  - Kc: FAO-56 (Allen et al., 1998) adaptado para BR (Embrapa Milho e Sorgo)
  - ETo: médias mensais INMET/Embrapa por macrorregião (cerrado, sp, ne)
  - CAD: Embrapa / Doorenbos & Pruitt (1977)
  - Taxa de infiltração básica: EMBRAPA / literatura brasileira
"""

from typing import Optional

# ── 1. CULTURAS E Kc ────────────────────────────────────────
# Kc por fase fenológica (FAO-56 / Embrapa):
#   ini  = fase inicial (germinação/estabelecimento)
#   med  = fase de máximo desenvolvimento / floração
#   fin  = fase de maturação / colheita
#   ciclo_dias = duração total do ciclo
#   z_rad_m    = profundidade efetiva do sistema radicular (m)
#   f_dep      = fração de depleção admissível (p — fator de estresse)

CULTURAS = {
    "soja": {
        "nome": "Soja",
        "Kc_ini": 0.40, "Kc_med": 1.15, "Kc_fin": 0.50,
        "fase_ini_d": 20, "fase_des_d": 35, "fase_med_d": 45, "fase_mat_d": 20,
        "ciclo_dias": 120,
        "z_rad_m": 0.60,
        "f_dep": 0.50,
        "obs": "Ciclo verão (nov–mar). Kc FAO-56 / Embrapa Soja.",
    },
    "milho": {
        "nome": "Milho",
        "Kc_ini": 0.30, "Kc_med": 1.20, "Kc_fin": 0.35,
        "fase_ini_d": 25, "fase_des_d": 30, "fase_med_d": 40, "fase_mat_d": 25,
        "ciclo_dias": 120,
        "z_rad_m": 0.70,
        "f_dep": 0.55,
        "obs": "Milho grão. Kc FAO-56. Safrinha: reduzir Kc_med para 1.10.",
    },
    "cana": {
        "nome": "Cana-de-açúcar",
        "Kc_ini": 0.40, "Kc_med": 1.25, "Kc_fin": 0.75,
        "fase_ini_d": 60, "fase_des_d": 90, "fase_med_d": 150, "fase_mat_d": 60,
        "ciclo_dias": 360,
        "z_rad_m": 1.20,
        "f_dep": 0.65,
        "obs": "Cana-planta 12 meses. Kc FAO-56 / ESALQ.",
    },
    "algodao": {
        "nome": "Algodão",
        "Kc_ini": 0.35, "Kc_med": 1.20, "Kc_fin": 0.50,
        "fase_ini_d": 30, "fase_des_d": 50, "fase_med_d": 55, "fase_mat_d": 45,
        "ciclo_dias": 180,
        "z_rad_m": 1.00,
        "f_dep": 0.65,
        "obs": "Algodão herbáceo. Kc FAO-56 / Embrapa Algodão.",
    },
    "feijao": {
        "nome": "Feijão",
        "Kc_ini": 0.35, "Kc_med": 1.15, "Kc_fin": 0.30,
        "fase_ini_d": 20, "fase_des_d": 25, "fase_med_d": 25, "fase_mat_d": 20,
        "ciclo_dias": 90,
        "z_rad_m": 0.50,
        "f_dep": 0.45,
        "obs": "Feijão comum. Kc FAO-56 / Embrapa Arroz e Feijão.",
    },
    "pastagem": {
        "nome": "Pastagem (Brachiaria/Tifton)",
        "Kc_ini": 0.85, "Kc_med": 1.00, "Kc_fin": 0.85,
        "fase_ini_d": 0, "fase_des_d": 0, "fase_med_d": 365, "fase_mat_d": 0,
        "ciclo_dias": 365,
        "z_rad_m": 0.45,
        "f_dep": 0.55,
        "obs": "Perene. Kc médio anual FAO-56 / Embrapa Pecuária.",
    },
    "sorgo": {
        "nome": "Sorgo granífero",
        "Kc_ini": 0.30, "Kc_med": 1.10, "Kc_fin": 0.55,
        "fase_ini_d": 20, "fase_des_d": 35, "fase_med_d": 40, "fase_mat_d": 25,
        "ciclo_dias": 120,
        "z_rad_m": 0.80,
        "f_dep": 0.55,
        "obs": "Kc FAO-56. Tolerante à seca — f_dep alto.",
    },
}

# ── 2. ETo POR MACRORREGIÃO (mm/dia, médias mensais históricas) ───
# Fonte: INMET — estações sinóticas / Embrapa
# Macrorregiões cobertas: cerrado (GO/MT/MS), sp (SP/MG sul),
#                         ne (BA/PI cerrado), pr (PR/SC), rs (RS)
ETO_REGIAO = {
    "cerrado": {  # GO, MT, MS, DF — altitude ~700-900m
        "descricao": "Cerrado (GO/MT/MS/DF)",
        "eto_mensal_mm_d": [5.5, 5.2, 4.8, 4.0, 3.5, 3.0,
                             3.2, 3.8, 4.5, 5.0, 5.2, 5.5],
        "eto_media_anual": 4.4,
    },
    "sp": {  # SP interior, MG sul — altitude ~500-800m
        "descricao": "SP interior / MG sul",
        "eto_mensal_mm_d": [5.0, 4.8, 4.5, 3.8, 3.2, 2.8,
                             3.0, 3.5, 4.2, 4.8, 5.0, 5.2],
        "eto_media_anual": 4.2,
    },
    "ne": {  # BA oeste, PI sul, TO — cerrado nordestino, semi-árido
        "descricao": "Cerrado nordestino (BA/PI/TO)",
        "eto_mensal_mm_d": [6.0, 5.8, 5.5, 5.0, 4.5, 4.2,
                             4.5, 5.0, 5.8, 6.2, 6.5, 6.2],
        "eto_media_anual": 5.4,
    },
    "pr": {  # PR, SC
        "descricao": "Sul (PR/SC)",
        "eto_mensal_mm_d": [4.5, 4.2, 3.8, 3.0, 2.5, 2.2,
                             2.5, 3.0, 3.5, 4.0, 4.2, 4.5],
        "eto_media_anual": 3.5,
    },
    "mg": {  # MG centro/norte, triângulo mineiro
        "descricao": "MG centro/Triângulo Mineiro",
        "eto_mensal_mm_d": [5.2, 5.0, 4.6, 3.9, 3.4, 3.0,
                             3.2, 3.7, 4.3, 5.0, 5.3, 5.4],
        "eto_media_anual": 4.3,
    },
}

# ── 3. SOLOS E CAD ──────────────────────────────────────────
# CAD = capacidade de água disponível (mm/m de solo)
# Fonte: Embrapa / Doorenbos & Pruitt 1977
SOLOS = {
    "arenoso": {
        "nome": "Arenoso (textura grossa)",
        "CAD_mm_m": 75,
        "TIB_mm_h": 30,   # taxa de infiltração básica
        "obs": "Latossolo vermelho-amarelo textura arenosa",
    },
    "franco_arenoso": {
        "nome": "Franco-arenoso",
        "CAD_mm_m": 110,
        "TIB_mm_h": 20,
        "obs": "Textura média-arenosa",
    },
    "franco": {
        "nome": "Franco (textura média)",
        "CAD_mm_m": 140,
        "TIB_mm_h": 12,
        "obs": "Latossolo vermelho textura média — mais comum no cerrado",
    },
    "franco_argiloso": {
        "nome": "Franco-argiloso",
        "CAD_mm_m": 160,
        "TIB_mm_h": 8,
        "obs": "Latossolo vermelho argiloso",
    },
    "argiloso": {
        "nome": "Argiloso (textura fina)",
        "CAD_mm_m": 180,
        "TIB_mm_h": 5,
        "obs": "> 60% argila — Latossolo roxo/nitossolo",
    },
}


# ── 4. FUNÇÕES PRINCIPAIS ────────────────────────────────────

def kc_medio(cultura_key: str) -> float:
    """Kc médio ponderado pelo tempo de cada fase (ciclo completo)."""
    c = CULTURAS[cultura_key]
    t_ini = c["fase_ini_d"]
    t_des = c["fase_des_d"]
    t_med = c["fase_med_d"]
    t_mat = c["fase_mat_d"]
    total = t_ini + t_des + t_med + t_mat
    if total == 0:
        return c["Kc_med"]
    # Kc desenvolvimento: interpolação linear ini→med
    kc_des = (c["Kc_ini"] + c["Kc_med"]) / 2
    kc_pond = (c["Kc_ini"]*t_ini + kc_des*t_des +
               c["Kc_med"]*t_med + c["Kc_fin"]*t_mat) / total
    return round(kc_pond, 3)


def calcular_lamina(
    cultura_key: str,
    regiao_key: str,
    solo_key: str,
    mes_plantio: int = 10,          # 1=jan … 12=dez
    fase: str = "med",              # ini / des / med / mat / medio
    eficiencia_aplicacao: float = 0.90,  # pivô: 85-92%
) -> dict:
    """
    Calcula a lâmina bruta de irrigação e o turno de rega.

    Retorna dict com:
      ETo_mm_d       : evapotranspiração de referência (mm/dia)
      Kc             : coeficiente de cultura na fase
      ETc_mm_d       : evapotranspiração da cultura (mm/dia)
      lamina_liq_mm  : lâmina líquida necessária (mm/evento)
      lamina_bruta_mm: lâmina bruta (mm/evento) — o que o pivô aplica
      turno_rega_d   : intervalo entre irrigações (dias)
      TAL_mm_h       : taxa de aplicação do pivô (calculada externamente)
      CAD_total_mm   : capacidade de água disponível total no perfil
      obs_solo       : observação sobre solo
    """
    cult  = CULTURAS[cultura_key]
    regiao = ETO_REGIAO[regiao_key]
    solo  = SOLOS[solo_key]

    # ETo do mês de plantio + 1 (fase de desenvolvimento típica)
    mes_idx = ((mes_plantio - 1) + 1) % 12   # mês seguinte ao plantio
    ETo = regiao["eto_mensal_mm_d"][mes_idx]

    # Kc conforme fase
    kc_map = {
        "ini": cult["Kc_ini"],
        "des": (cult["Kc_ini"] + cult["Kc_med"]) / 2,
        "med": cult["Kc_med"],
        "mat": cult["Kc_fin"],
        "medio": kc_medio(cultura_key),
    }
    Kc = kc_map.get(fase, cult["Kc_med"])

    ETc = round(ETo * Kc, 2)

    # CAD total no perfil radicular
    CAD_total = solo["CAD_mm_m"] * cult["z_rad_m"]

    # Lâmina líquida por evento (depleção admissível)
    lam_liq = round(CAD_total * cult["f_dep"], 1)

    # Turno de rega (dias)
    turno = max(1, round(lam_liq / ETc)) if ETc > 0 else 7

    # Lâmina bruta (o que o pivô precisa aplicar)
    lam_bruta = round(lam_liq / eficiencia_aplicacao, 1)

    # Lâmina diária equivalente (lam_bruta / turno)
    lam_dia = round(lam_bruta / turno, 2)

    return {
        "cultura":          cult["nome"],
        "regiao":           regiao["descricao"],
        "solo":             solo["nome"],
        "fase":             fase,
        "mes_plantio":      mes_plantio,
        "ETo_mm_d":         round(ETo, 2),
        "Kc":               round(Kc, 3),
        "ETc_mm_d":         ETc,
        "CAD_total_mm":     round(CAD_total, 1),
        "f_dep":            cult["f_dep"],
        "lamina_liq_mm":    lam_liq,
        "eficiencia_aplic": eficiencia_aplicacao,
        "lamina_bruta_mm":  lam_bruta,
        "turno_rega_d":     turno,
        "lamina_dia_mm":    lam_dia,
        "ciclo_dias":       cult["ciclo_dias"],
        "z_rad_m":          cult["z_rad_m"],
        "TIB_solo_mm_h":    solo["TIB_mm_h"],
        "obs_cultura":      cult["obs"],
    }


def verificar_taxa_aplicacao(
    lamina_dia_mm: float,
    horas_operacao: float,
    raio_m: float,
    TIB_solo_mm_h: float,
) -> dict:
    """
    Verifica se a taxa de aplicação do pivô excede a TIB do solo.

    TAL (Taxa de Aplicação Local) em mm/h = lâmina_dia / horas_op
    (simplificação para pivô em rotação contínua).
    """
    TAL = round(lamina_dia_mm / horas_operacao, 2) if horas_operacao > 0 else 0
    risco = TAL > TIB_solo_mm_h
    return {
        "TAL_mm_h":     TAL,
        "TIB_mm_h":     TIB_solo_mm_h,
        "risco_runoff": risco,
        "status":       "ALERTA — risco de enxurrada" if risco else "OK",
        "recomendacao": (
            "Reduzir lâmina por evento ou aumentar turno de rega. "
            "Considerar solo com maior TIB ou fracionamento da irrigação."
            if risco else
            "Taxa de aplicação adequada para o solo."
        ),
    }


def calcular_demanda_total(
    cultura_key: str,
    regiao_key: str,
    area_ha: float,
    eficiencia: float = 0.90,
) -> dict:
    """
    Estima a demanda hídrica total do ciclo (m³).
    Usa Kc médio ponderado x ETo médio anual x área.
    """
    cult   = CULTURAS[cultura_key]
    regiao = ETO_REGIAO[regiao_key]
    Kc_m   = kc_medio(cultura_key)
    ETo_m  = regiao["eto_media_anual"]
    ETc_m  = ETo_m * Kc_m
    # volume total bruto por ciclo (m³)
    vol = area_ha * 10000 * (ETc_m * cult["ciclo_dias"] / 1000) / eficiencia
    return {
        "cultura":          cult["nome"],
        "ciclo_dias":       cult["ciclo_dias"],
        "Kc_medio":         Kc_m,
        "ETo_medio_mm_d":   ETo_m,
        "ETc_medio_mm_d":   round(ETc_m, 2),
        "ETc_ciclo_mm":     round(ETc_m * cult["ciclo_dias"], 1),
        "vol_bruto_m3":     round(vol, 0),
        "area_ha":          area_ha,
    }


def listar_culturas() -> list:
    return [{"key": k, "nome": v["nome"], "ciclo_d": v["ciclo_dias"]}
            for k, v in CULTURAS.items()]

def listar_regioes() -> list:
    return [{"key": k, "nome": v["descricao"],
             "eto_media": v["eto_media_anual"]}
            for k, v in ETO_REGIAO.items()]

def listar_solos() -> list:
    return [{"key": k, "nome": v["nome"],
             "CAD_mm_m": v["CAD_mm_m"], "TIB_mm_h": v["TIB_mm_h"]}
            for k, v in SOLOS.items()]
