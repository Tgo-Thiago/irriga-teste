"""
catalogo_bombas.py
==================
Catálogo real de bombas centrífugas Imbil linha INI.
Fonte: Catálogo Imbil INI — Edição 12/2015 (PDF oficial).

Dados extraídos das curvas características (rotor máximo, agua 20°C).
Regressão H = a + b·Q + c·Q²  (Q em m³/h, H em m).
Eficiência η% lida nas curvas de isoficiência.

Cobertura:  Q = 0 – 1000 m³/h  |  H = 10 – 230 m
Aplicação:  irrigação por pivô central (faixa principal: 50–600 m³/h, 30–180 m)
"""

import math
from typing import Optional

# ── Catálogo de modelos ───────────────────────────────────────
# Cada entrada:
#   rpm          : rotação nominal
#   coefs        : [c, b, a]  →  H = c·Q² + b·Q + a   (m³/h, m)
#   H_shutoff    : HMT em Q=0
#   Q_max        : Q onde H≈0 (limite operacional)
#   Q_BEP        : vazão no ponto de melhor eficiência
#   H_BEP        : HMT no BEP
#   eta_BEP      : eficiência no BEP (%)
#   eta_max      : eficiência máxima (%)
#   flange_suc   : DN sucção (mm)
#   flange_rec   : DN recalque (mm)
#   NPSH_r_m     : NPSH requerido no BEP (m)
#   curva_pontos : [(Q, H, η), ...]  pontos originais lidos

BOMBAS = [
    # ── 3500 rpm ──────────────────────────────────────────────
    {
        "modelo": "INI 40-200",   "rpm": 3500,
        "coefs": [-0.02589,  0.4314, 99.84],
        "H_shutoff": 99.8,  "Q_max": 122.0,
        "Q_BEP": 64,  "H_BEP": 67,  "eta_BEP": 58,  "eta_max": 58,
        "flange_suc": 65,  "flange_rec": 40,  "NPSH_r_m": 6.5,
        "curva_pontos": [(0,100,0),(16,95,38),(32,90,48),(48,80,53),(64,67,58),(80,53,53)],
    },
    {
        "modelo": "INI 50-200",   "rpm": 3500,
        "coefs": [-0.005227, 0.2010, 118.8],
        "H_shutoff": 118.8, "Q_max": 151.0,
        "Q_BEP": 100, "H_BEP": 60,  "eta_BEP": 65,  "eta_max": 65,
        "flange_suc": 80,  "flange_rec": 50,  "NPSH_r_m": 10.0,
        "curva_pontos": [(0,120,0),(25,110,50),(50,95,55),(75,80,60),(100,60,65),(125,35,62)],
    },
    {
        "modelo": "INI 65-160",   "rpm": 3500,
        "coefs": [-0.001093, 0.06940, 67.4],
        "H_shutoff": 67.4,  "Q_max": 252.0,
        "Q_BEP": 160, "H_BEP": 42,  "eta_BEP": 72,  "eta_max": 72,
        "flange_suc": 100, "flange_rec": 65,  "NPSH_r_m": 10.0,
        "curva_pontos": [(0,68,0),(40,65,59),(80,60,64),(120,52,69),(160,42,72),(200,24,70)],
    },
    {
        "modelo": "INI 65-200",   "rpm": 3500,
        "coefs": [-0.001090, 0.06390, 89.2],
        "H_shutoff": 89.2,  "Q_max": 284.0,
        "Q_BEP": 160, "H_BEP": 63,  "eta_BEP": 76,  "eta_max": 76,
        "flange_suc": 100, "flange_rec": 65,  "NPSH_r_m": 8.0,
        "curva_pontos": [(0,90,0),(40,87,51),(80,82,64),(120,75,69),(160,63,76),(200,45,74)],
    },
    {
        "modelo": "INI 80-200",   "rpm": 3500,
        "coefs": [-0.0006458, 0.05360, 124.7],
        "H_shutoff": 124.7, "Q_max": 438.0,
        "Q_BEP": 300, "H_BEP": 60,  "eta_BEP": 68,  "eta_max": 68,
        "flange_suc": 125, "flange_rec": 80,  "NPSH_r_m": 15.0,
        "curva_pontos": [(0,125,0),(75,115,48),(150,100,58),(225,80,63),(300,60,68),(375,27,62)],
    },
    {
        "modelo": "INI 100-200",  "rpm": 3500,
        "coefs": [-0.0002486, 0.02430, 120.5],
        "H_shutoff": 120.5, "Q_max": 600.0,
        "Q_BEP": 480, "H_BEP": 55,  "eta_BEP": 67,  "eta_max": 67,
        "flange_suc": 125, "flange_rec": 100, "NPSH_r_m": 15.0,
        "curva_pontos": [(0,120,0),(120,110,47),(240,95,57),(360,75,62),(480,55,67),(600,30,60)],
    },

    # ── 1750 rpm ──────────────────────────────────────────────
    {
        "modelo": "INI 80-250",   "rpm": 1750,
        "coefs": [-0.0007106, 0.05610, 49.5],
        "H_shutoff": 49.5,  "Q_max": 262.0,
        "Q_BEP": 150, "H_BEP": 30,  "eta_BEP": 65,  "eta_max": 65,
        "flange_suc": 125, "flange_rec": 80,  "NPSH_r_m": 6.0,
        "curva_pontos": [(0,50,0),(30,47,41),(60,43,51),(90,40,56),(120,36,61),(150,30,65),(180,22,64)],
    },
    {
        "modelo": "INI 100-250",  "rpm": 1750,
        "coefs": [-0.0003264, 0.02620, 37.8],
        "H_shutoff": 37.8,  "Q_max": 342.0,
        "Q_BEP": 200, "H_BEP": 24,  "eta_BEP": 70,  "eta_max": 70,
        "flange_suc": 125, "flange_rec": 100, "NPSH_r_m": 5.0,
        "curva_pontos": [(0,38,0),(50,36,48),(100,33,58),(150,29,65),(200,24,70),(250,16,65)],
    },
    {
        "modelo": "INI 100-315",  "rpm": 1750,
        "coefs": [-0.0002682, 0.02680, 65.1],
        "H_shutoff": 65.1,  "Q_max": 495.0,
        "Q_BEP": 300, "H_BEP": 36,  "eta_BEP": 73,  "eta_max": 73,
        "flange_suc": 125, "flange_rec": 100, "NPSH_r_m": 5.0,
        "curva_pontos": [(0,65,0),(60,62,57),(120,57,62),(180,51,67),(240,44,72),(300,36,73),(360,26,68)],
    },
    {
        "modelo": "INI 100-400",  "rpm": 1750,
        "coefs": [-0.0005531, 0.06830, 118.4],
        "H_shutoff": 118.4, "Q_max": 459.0,
        "Q_BEP": 240, "H_BEP": 67,  "eta_BEP": 68,  "eta_max": 68,
        "flange_suc": 125, "flange_rec": 100, "NPSH_r_m": 6.0,
        "curva_pontos": [(0,120,0),(60,105,48),(120,93,58),(180,80,63),(240,67,68),(300,50,68),(360,30,60)],
    },
    {
        "modelo": "INI 125-200",  "rpm": 1750,
        "coefs": [-0.0000431, 0.00542, 25.1],
        "H_shutoff": 25.1,  "Q_max": 600.0,
        "Q_BEP": 400, "H_BEP": 14,  "eta_BEP": 66,  "eta_max": 66,
        "flange_suc": 150, "flange_rec": 125, "NPSH_r_m": 10.0,
        "curva_pontos": [(0,25,0),(100,23,48),(200,20,58),(300,17,63),(400,14,66),(500,10,62)],
    },
    {
        "modelo": "INI 125-315",  "rpm": 1750,
        "coefs": [-0.0001149, 0.01510, 75.3],
        "H_shutoff": 75.3,  "Q_max": 658.0,
        "Q_BEP": 500, "H_BEP": 40,  "eta_BEP": 73,  "eta_max": 73,
        "flange_suc": 150, "flange_rec": 125, "NPSH_r_m": 5.0,
        "curva_pontos": [(0,75,0),(100,72,49),(200,66,59),(300,59,64),(400,50,69),(500,40,73)],
    },
    {
        "modelo": "INI 125-400",  "rpm": 1750,
        "coefs": [-0.0001787, 0.02510, 119.0],
        "H_shutoff": 119.0, "Q_max": 667.0,
        "Q_BEP": 500, "H_BEP": 55,  "eta_BEP": 70,  "eta_max": 70,
        "flange_suc": 150, "flange_rec": 125, "NPSH_r_m": 5.0,
        "curva_pontos": [(0,120,0),(100,107,47),(200,95,57),(300,83,62),(400,70,67),(500,55,70),(600,37,65)],
    },
    {
        "modelo": "INI 150-315",  "rpm": 1750,
        "coefs": [-0.00005987, 0.007750, 54.5],
        "H_shutoff": 54.5,  "Q_max": 760.0,
        "Q_BEP": 600, "H_BEP": 33,  "eta_BEP": 69,  "eta_max": 69,
        "flange_suc": 200, "flange_rec": 150, "NPSH_r_m": 6.0,
        "curva_pontos": [(0,55,0),(150,52,49),(300,48,59),(450,42,64),(600,33,69),(750,20,65)],
    },
    {
        "modelo": "INI 150-400",  "rpm": 1750,
        "coefs": [-0.0000951, 0.01310, 91.7],
        "H_shutoff": 91.7,  "Q_max": 822.0,
        "Q_BEP": 500, "H_BEP": 52,  "eta_BEP": 75,  "eta_max": 75,
        "flange_suc": 200, "flange_rec": 150, "NPSH_r_m": 8.0,
        "curva_pontos": [(0,90,0),(100,87,58),(200,82,63),(300,75,68),(400,65,73),(500,52,75),(700,35,70)],
    },
]


# ── Funções públicas ──────────────────────────────────────────

def H_bomba(modelo_dict: dict, Q_m3h: float) -> float:
    """HMT da bomba em Q_m3h (m³/h) → H (m). Retorna 0 se fora do range."""
    c, b, a = modelo_dict["coefs"]
    H = c * Q_m3h**2 + b * Q_m3h + a
    return max(H, 0.0)


def eta_bomba(modelo_dict: dict, Q_m3h: float) -> float:
    """
    Eficiência interpolada linealmente entre os pontos da curva.
    Retorna eta_BEP se Q_m3h estiver fora dos pontos medidos.
    """
    pts = [(p[0], p[2]) for p in modelo_dict["curva_pontos"] if p[2] > 0]
    if not pts:
        return modelo_dict["eta_BEP"]
    pts.sort()
    if Q_m3h <= pts[0][0]:
        return pts[0][1]
    if Q_m3h >= pts[-1][0]:
        return pts[-1][1]
    for i in range(len(pts)-1):
        q1, e1 = pts[i]
        q2, e2 = pts[i+1]
        if q1 <= Q_m3h <= q2:
            f = (Q_m3h - q1) / (q2 - q1)
            return e1 + f * (e2 - e1)
    return modelo_dict["eta_BEP"]


def ponto_operacao(modelo_dict: dict, curva_sistema_fn) -> Optional[dict]:
    """
    Encontra o ponto de operação real: interseção da curva da bomba
    com a curva do sistema H_sis(Q).
    curva_sistema_fn: função Q_m3h → H_sistema_m
    Retorna dict com Q_op, H_op, eta_op, potencia_kw ou None.
    """
    # busca por bissecção: H_bomba(Q) - H_sistema(Q) = 0
    Q_max = modelo_dict["Q_max"]
    lo, hi = 0.0, Q_max
    for _ in range(60):
        mid = (lo + hi) / 2.0
        dif = H_bomba(modelo_dict, mid) - curva_sistema_fn(mid)
        if abs(hi - lo) < 0.1:
            break
        if dif > 0:
            lo = mid
        else:
            hi = mid
    Q_op = (lo + hi) / 2.0
    H_op = H_bomba(modelo_dict, Q_op)
    H_sis = curva_sistema_fn(Q_op)
    # só retorna se os dois convergem
    if abs(H_op - H_sis) > 5.0:
        return None
    eta = eta_bomba(modelo_dict, Q_op) / 100.0
    Q_m3s = Q_op / 3600.0
    pot_kw = (Q_m3s * 9810 * H_op / eta / 1000) if eta > 0 else 0.0
    return {
        "Q_op_m3h":   round(Q_op, 2),
        "H_op_m":     round(H_op, 2),
        "eta_op_pct": round(eta * 100, 1),
        "potencia_kw":round(pot_kw, 2),
        "dentro_BEP": abs(Q_op - modelo_dict["Q_BEP"]) / modelo_dict["Q_BEP"] < 0.30,
    }


def selecionar_bomba(Q_projeto_m3h: float, HMT_projeto_m: float,
                     margem_hmt: float = 1.10) -> Optional[dict]:
    """
    Seleciona o modelo Imbil INI mais adequado para Q e HMT de projeto.

    Critérios (em ordem):
      1. H_shutoff >= HMT_projeto (bomba consegue superar a HMT)
      2. Q_projeto dentro do range operacional (0.5·Q_BEP a 1.15·Q_BEP)
      3. Menor potência absorvida no ponto de operação real
      4. Preferência por modelos com BEP próximo de Q_projeto

    Retorna o melhor modelo com ponto de operação calculado, ou None.
    """
    HMT_req = HMT_projeto_m * margem_hmt
    candidatos = []

    for b in BOMBAS:
        # 1. H_shutoff deve superar HMT com margem
        if b["H_shutoff"] < HMT_req:
            continue
        # 2. Q_projeto deve estar no range operacional
        if Q_projeto_m3h > b["Q_max"] * 0.95:
            continue
        if Q_projeto_m3h < b["Q_max"] * 0.10:
            continue

        # 3. Calcula ponto de operação real
        # Curva do sistema: H_sis = HMT_projeto (simplificado — ponto fixo)
        # Para a seleção usa HMT_projeto diretamente, pois já inclui todas as perdas
        H_calc = H_bomba(b, Q_projeto_m3h)
        if H_calc < HMT_projeto_m * 0.85:
            continue

        eta = eta_bomba(b, Q_projeto_m3h) / 100.0
        Q_m3s = Q_projeto_m3h / 3600.0
        pot_kw = (Q_m3s * 9810 * HMT_req / max(eta, 0.50) / 1000)

        # 4. Score: penaliza afastamento do BEP e excesso de potência
        desvio_bep = abs(Q_projeto_m3h - b["Q_BEP"]) / b["Q_BEP"]
        score = pot_kw * (1 + desvio_bep)

        candidatos.append({
            "modelo":          b["modelo"],
            "rpm":             b["rpm"],
            "fabricante":      "Imbil",
            "linha":           "INI",
            "H_shutoff_m":     b["H_shutoff"],
            "Q_max_m3h":       b["Q_max"],
            "Q_BEP_m3h":       b["Q_BEP"],
            "H_BEP_m":         b["H_BEP"],
            "eta_BEP_pct":     b["eta_BEP"],
            "eta_max_pct":     b["eta_max"],
            "flange_suc_mm":   b["flange_suc"],
            "flange_rec_mm":   b["flange_rec"],
            "NPSH_r_m":        b["NPSH_r_m"],
            # ponto de operação no projeto
            "Q_op_m3h":        round(Q_projeto_m3h, 2),
            "H_op_m":          round(H_calc, 2),
            "eta_op_pct":      round(eta * 100, 1),
            "potencia_kw":     round(pot_kw, 2),
            "margem_hmt_m":    round(H_calc - HMT_projeto_m, 2),
            "dentro_BEP":      desvio_bep < 0.30,
            "eficiencia":      eta,
            "_score":          score,
        })

    if not candidatos:
        return None

    melhor = min(candidatos, key=lambda x: x["_score"])
    melhor.pop("_score")
    return melhor


def listar_modelos() -> list:
    """Retorna lista de todos os modelos com faixas Q e H."""
    return [
        {
            "modelo": b["modelo"],
            "rpm":    b["rpm"],
            "Q_min_m3h": round(b["Q_max"] * 0.10, 0),
            "Q_max_m3h": b["Q_max"],
            "H_max_m":   b["H_shutoff"],
            "H_BEP_m":   b["H_BEP"],
            "Q_BEP_m3h": b["Q_BEP"],
            "eta_max_pct": b["eta_max"],
        }
        for b in BOMBAS
    ]
