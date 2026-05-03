"""
telescopia.py
=============
Monta a configuração de vãos e diâmetros do pivô central.

Catálogo de vãos (comprimentos reais de mercado)
-------------------------------------------------
  longo    = 54.55 m
  médio    = 47.85 m
  pequeno  = 41.15 m
  L3       = 21.10 m  ← balanço, SEMPRE o último vão

Catálogo de diâmetros (maior → menor)
--------------------------------------
  10"      = 254.0 mm
  8 5/8"   = 219.1 mm
  6 5/8"   = 168.3 mm
  5 9/16"  = 141.3 mm

Regras de montagem
------------------
1. Vãos sempre do maior (longo) para o menor (pequeno)
2. L3 é sempre o último vão (balanço do pivô)
3. Diâmetros sempre decrescentes (centro → fim)
4. Diâmetro de cada vão: o MAIOR que mantém 0.5 ≤ v ≤ 2.0 m/s
5. Nunca um vão mais externo pode ter diâmetro maior que o anterior
"""

import math

# ── Catálogo ──────────────────────────────────────────────────

VAOS_CATALOG = [
    {"tipo": "longo",   "comp": 54.55},   # maior primeiro
    {"tipo": "medio",   "comp": 47.85},
    {"tipo": "pequeno", "comp": 41.15},   # menor por último
]

BALANCO = {"tipo": "L3", "comp": 21.10}   # sempre o último

DIAMETROS_PIVO = [
    {"nome": '10"',     "m": 0.2540},     # maior primeiro
    {"nome": '8 5/8"',  "m": 0.2191},
    {"nome": '6 5/8"',  "m": 0.1683},
    {"nome": '5 9/16"', "m": 0.1413},     # menor por último
]

V_MIN_PIVO = 0.5   # m/s — mínimo aceitável
V_MAX_PIVO = 2.0   # m/s — máximo aceitável
TOL = 0.05         # m — tolerância de fechamento


# ── Hidráulica base ───────────────────────────────────────────

def _area_secao(D_m: float) -> float:
    return math.pi * (D_m / 2) ** 2


def _q_proporcional_m3s(Q_total_m3s: float, raio_real: float, r_ini: float) -> float:
    """
    Q no início do vão que começa em r_ini.
    Proporcional à área irrigada ainda não coberta: A_restante / A_total.
    """
    if raio_real <= 0:
        return Q_total_m3s
    frac = (raio_real**2 - r_ini**2) / raio_real**2
    return Q_total_m3s * max(frac, 0.0)


# ── Montagem dos vãos ─────────────────────────────────────────

def montar_vaos(raio_desejado: float) -> list:
    """
    Retorna lista de vãos que cobre raio_desejado, obedecendo:
    - Vãos do maior para o menor
    - L3 sempre no final
    - raio_real >= raio_desejado (nunca deixa área irrigada descoberta)

    Cada item: {"tipo", "comp", "balanco"}
    """
    # espaço disponível para os vãos principais (L3 reservado)
    espaco = raio_desejado - BALANCO["comp"]

    if espaco <= 0:
        return [{"tipo": BALANCO["tipo"], "comp": BALANCO["comp"], "balanco": True}]

    vaos = []
    restante = espaco

    # greedy: do maior para o menor
    for vao in VAOS_CATALOG:
        comp = vao["comp"]
        while restante >= comp - TOL:
            vaos.append({"tipo": vao["tipo"], "comp": comp, "balanco": False})
            restante -= comp
            # para de usar este tipo quando o restante não comporta mais
            if restante < VAOS_CATALOG[-1]["comp"] - TOL:
                break

    # se sobrou espaço (< menor vão), adiciona o menor vão disponível
    # o raio real ficará ligeiramente maior que o desejado — comportamento real
    if restante > TOL:
        vaos.append({"tipo": VAOS_CATALOG[-1]["tipo"],
                     "comp": VAOS_CATALOG[-1]["comp"],
                     "balanco": False})

    # L3 sempre no final
    vaos.append({"tipo": BALANCO["tipo"], "comp": BALANCO["comp"], "balanco": True})

    return vaos


# ── Seleção de diâmetro por vão ───────────────────────────────

def diametro_por_vao(Q_m3s: float, diam_anterior_m: float) -> dict:
    """
    Retorna o maior diâmetro que:
      1. É <= diâmetro do vão anterior (nunca aumenta de diâmetro)
      2. Mantém V_MIN <= v <= V_MAX

    Se nenhum satisfaz ambas as restrições, retorna o maior candidato
    disponível (garante que o diâmetro nunca aumenta).

    Retorna: {"nome", "m", "velocidade_m_s"}
    """
    # candidatos: diâmetros <= anterior (lista já em ordem decrescente)
    candidatos = [d for d in DIAMETROS_PIVO if d["m"] <= diam_anterior_m + 1e-4]

    if not candidatos:
        candidatos = [DIAMETROS_PIVO[-1]]  # último recurso

    # do maior para o menor: primeiro que cabe na faixa de velocidade
    for d in candidatos:
        v = Q_m3s / _area_secao(d["m"])
        if V_MIN_PIVO <= v <= V_MAX_PIVO:
            return {**d, "velocidade_m_s": round(v, 4)}

    # nenhum na faixa: retorna o maior candidato (velocidade mais baixa = mais seguro)
    d = candidatos[0]
    v = Q_m3s / _area_secao(d["m"])
    return {**d, "velocidade_m_s": round(v, 4)}


# ── Função principal ──────────────────────────────────────────

def configurar_telescopia(raio_desejado: float, Q_total_m3h: float) -> dict:
    """
    Monta e dimensiona o pivô completo.

    Parâmetros
    ----------
    raio_desejado : float — raio desejado pelo usuário (m)
    Q_total_m3h   : float — vazão total calculada pela lâmina (m³/h)

    Retorna
    -------
    {
      vaos        : lista de vãos com diâmetro, velocidade, Q, etc.
      raio_real   : float — comprimento real do pivô (m)
      raio_desejado : float
      delta_m     : raio_real - raio_desejado
      resumo      : dict com contagens e comprimentos por tipo/diâmetro
    }
    """
    vaos_brutos = montar_vaos(raio_desejado)
    raio_real   = sum(v["comp"] for v in vaos_brutos)
    Q_total_m3s = Q_total_m3h / 3600.0

    vaos_final  = []
    r           = 0.0
    diam_ant_m  = DIAMETROS_PIVO[0]["m"]   # começa com 10" (maior)

    for vao in vaos_brutos:
        comp = vao["comp"]

        # Q proporcional à área irrigada restante neste ponto
        Q_local = _q_proporcional_m3s(Q_total_m3s, raio_real, r)

        d = diametro_por_vao(Q_local, diam_ant_m)
        diam_ant_m = d["m"]

        vaos_final.append({
            "indice":          len(vaos_final) + 1,
            "tipo":            vao["tipo"],
            "r_ini_m":         round(r, 3),
            "r_fim_m":         round(r + comp, 3),
            "comprimento_m":   round(comp, 3),
            "balanco":         vao.get("balanco", False),
            "diametro_nominal":d["nome"],
            "diametro_m":      d["m"],
            "diametro_mm":     round(d["m"] * 1000, 1),
            "Q_in_m3h":        round(Q_local * 3600, 3),
            "velocidade_m_s":  d["velocidade_m_s"],
        })

        r += comp

    # resumo por tipo de vão
    resumo_vaos = {}
    for v in vaos_final:
        t = v["tipo"]
        resumo_vaos.setdefault(t, {"quantidade": 0, "comprimento_total_m": 0.0})
        resumo_vaos[t]["quantidade"] += 1
        resumo_vaos[t]["comprimento_total_m"] += v["comprimento_m"]

    # resumo por diâmetro
    resumo_diams = {}
    for v in vaos_final:
        k = v["diametro_nominal"]
        resumo_diams.setdefault(k, {"quantidade": 0, "comprimento_total_m": 0.0})
        resumo_diams[k]["quantidade"] += 1
        resumo_diams[k]["comprimento_total_m"] += v["comprimento_m"]

    return {
        "vaos":            vaos_final,
        "raio_real":       round(raio_real, 2),
        "raio_desejado":   round(raio_desejado, 2),
        "delta_m":         round(raio_real - raio_desejado, 2),
        "n_vaos":          len(vaos_final),
        "resumo_vaos":     resumo_vaos,
        "resumo_diametros":resumo_diams,
    }


# ── Compatibilidade com código legado ─────────────────────────

def gerar_configuracao_vaos(raio: float) -> list:
    """
    Mantida para compatibilidade com módulos que ainda chamam esta função.
    Retorna lista simples de vãos (sem diâmetros — esses são atribuídos
    depois pelo motor hidráulico).
    """
    return [
        {
            "tipo":         v["tipo"],
            "comprimento_m":v["comp"],
            "balanco":      v.get("balanco", False),
        }
        for v in montar_vaos(raio)
    ]
