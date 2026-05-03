"""
motor_pivo.py — motor hidráulico definitivo do pivô central.

Funcionalidades integradas
--------------------------
1. Catálogo real Senninger i-WOB2 (41 bocais, k e x medidos)
2. Telescopia correta: 10" → 8 5/8" → 6 5/8" → 5 9/16"
3. Validação antecipada: Q > Q_max_10" → alerta CRÍTICO
4. Reguladores de pressão obrigatórios quando P > 10.5 mca
5. Modelo angular (velocidade_percentual > 0):
     t_volta, n_voltas, lam/volta, q_bocal(r) proporcional à v_local
6. Compatibilidade total com versões anteriores
"""

import math
from typing import Optional

P_MIN_FINAL   = 10.0
P_MAX_BOCAL   = 10.54
P_IDEAL_BOCAL = 7.03
C_HW          = 130

Q_MAX_10POL_M3H = 366.0
Q_RECOM_MAX_M3H = 300.0

VAOS_CATALOG = [
    {"tipo": "longo",   "comp": 54.55},
    {"tipo": "medio",   "comp": 47.85},
    {"tipo": "pequeno", "comp": 41.15},
]
BALANCO = {"tipo": "L3", "comp": 21.10}

DIAMETROS_PIVO = [
    {"nome": '10"',     "m": 0.2540},
    {"nome": '8 5/8"',  "m": 0.2191},
    {"nome": '6 5/8"',  "m": 0.1683},
    {"nome": '5 9/16"', "m": 0.1413},
]

V_MIN = 0.5
V_MAX = 2.0
TOL   = 0.05


def _A(D):              return math.pi * (D/2)**2
def _area_anel(r0, r1): return math.pi * (r1**2 - r0**2)

def _hw(Q, D, L, C=C_HW):
    if Q <= 1e-9 or D <= 0 or L <= 0: return 0.0
    return 10.67 * L * (Q**1.852) / ((C**1.852) * (D**4.87))

def _q_nec_continuo(lam_h, r0, r1):
    return (lam_h / 1000.0) * _area_anel(r0, r1)

def _q_nec_angular(lam_volta_mm, r_med, raio_real, v_max, vel_pct, esp):
    if r_med <= 0 or raio_real <= 0: return 0.0
    v_local = v_max * (vel_pct / 100.0) * (r_med / raio_real)
    if v_local <= 0: return 0.0
    return (lam_volta_mm / 1000.0) * v_local * (esp ** 2) * 60.0

def _lam_mm_h(q, r0, r1):
    a = _area_anel(r0, r1)
    return (q / a) * 1000.0 if a > 0 and q > 0 else 0.0

def _cota(perf, pos):
    if not perf: return 0.0
    if pos <= perf[0]["x"]: return perf[0]["z"]
    if pos >= perf[-1]["x"]: return perf[-1]["z"]
    for i in range(len(perf)-1):
        p1, p2 = perf[i], perf[i+1]
        if p1["x"] <= pos <= p2["x"]:
            f = (pos-p1["x"])/(p2["x"]-p1["x"])
            return p1["z"] + f*(p2["z"]-p1["z"])
    return perf[-1]["z"]

def _dz(perf, r0, r1): return _cota(perf, r1) - _cota(perf, r0)


def _montar_vaos(raio_desejado):
    espaco = raio_desejado - BALANCO["comp"]
    if espaco <= 0:
        return [{"tipo": BALANCO["tipo"], "comp": BALANCO["comp"], "balanco": True}]
    vaos, restante = [], espaco
    for vao in VAOS_CATALOG:
        comp = vao["comp"]
        while restante >= comp - TOL:
            vaos.append({"tipo": vao["tipo"], "comp": comp, "balanco": False})
            restante -= comp
            if restante < VAOS_CATALOG[-1]["comp"] - TOL:
                break
    if restante > TOL:
        vaos.append({"tipo": VAOS_CATALOG[-1]["tipo"],
                     "comp": VAOS_CATALOG[-1]["comp"], "balanco": False})
    vaos.append({"tipo": BALANCO["tipo"], "comp": BALANCO["comp"], "balanco": True})
    return vaos

def _diametro_vao(Q_m3s, diam_ant):
    """
    Telescopia fiel à prática de campo:
    - Mantém o diâmetro atual enquanto v >= V_CONFORTO (0.9 m/s)
    - Quando v cai abaixo de V_CONFORTO, reduz para o PRÓXIMO menor
      que ainda mantém V_MIN <= v <= V_MAX
    - Nunca aumenta o diâmetro
    - Produz sequência natural: 10" → 8 5/8" → 6 5/8" → 5 9/16"
    """
    V_CONFORTO = 0.9   # m/s — abaixo disso reduz para o próximo menor

    candidatos = [d for d in DIAMETROS_PIVO if d["m"] <= diam_ant + 1e-4]
    if not candidatos:
        candidatos = [DIAMETROS_PIVO[-1]]

    d_atual = candidatos[0]              # maior disponível (= diâmetro anterior)
    v_atual = Q_m3s / _A(d_atual["m"])

    # velocidade confortável → mantém o diâmetro atual
    if v_atual >= V_CONFORTO:
        return d_atual

    # velocidade caindo → tenta o próximo menor que cabe na faixa
    for d in candidatos[1:]:             # do próximo menor em diante
        v = Q_m3s / _A(d["m"])
        if V_MIN <= v <= V_MAX:
            return d

    # nenhum menor funciona → mantém atual (evita velocidade < V_MIN)
    return d_atual


def _emissor_catalogo(q_nec, P_med, n_bocais, modelo, P_proj):
    try:
        from app.core.catalogo_bocais import selecionar_bocal, P_MIN_MCA, P_MAX_MCA
        q_pb = q_nec / max(n_bocais, 1)
        bocal = selecionar_bocal(q_pb, min(P_med, P_MAX_MCA),
                                  modelo or "preto", min(P_proj or P_med, P_MAX_MCA))
        if bocal is None: return None
        k_ef = bocal["k_m3h"] * n_bocais
        x_ef = bocal["x"]
        P_c  = min(P_med, P_MAX_MCA)
        q_ef = k_ef * (P_c**x_ef) if P_c > 0 else 0.0
        P_nec = (q_nec/k_ef)**(1/x_ef) if k_ef > 0 else 0.0
        deficit = max(P_nec - P_med, 0.0)
        flags = []
        if P_med > P_MAX_MCA:
            flags.append(f"REGULADOR OBRIGATÓRIO: P={P_med:.1f} mca > máx bocal "
                         f"#{bocal['numero']} ({P_MAX_MCA:.1f} mca). Instalar PSR-2.")
        elif P_med < P_MIN_MCA:
            flags.append(f"CRÍTICO: P={P_med:.1f} mca < mín bocal "
                         f"#{bocal['numero']} ({P_MIN_MCA:.1f} mca).")
        return {
            "k_efetivo": round(k_ef,4), "x_efetivo": round(x_ef,4),
            "q_entregue": round(q_nec if deficit<=0 else q_ef, 5),
            "P_nec": round(P_nec,2), "deficit": round(deficit,2),
            "bocal_numero": bocal["numero"], "bocal_cor": bocal["cor"],
            "bocal_orificio_mm": bocal["orificio_mm"],
            "bocal_k": bocal["k_m3h"], "bocal_x": bocal["x"],
            "q_por_bocal_l_h": round(q_pb*1000,1),
            "dentro_da_faixa": P_MIN_MCA <= P_med <= P_MAX_MCA,
            "regulador_necessario": P_med > P_MAX_MCA, "flags": flags,
        }
    except ImportError:
        return None

def _emissor_generico(q_nec, P_med, n_bocais, k, x):
    k_ef = k * n_bocais
    P_nec = (q_nec/k_ef)**(1/x) if k_ef > 0 and q_nec > 0 else 0.0
    deficit = max(P_nec - P_med, 0.0)
    q_ef = k_ef*(P_med**x) if P_med > 0 else 0.0
    return {
        "k_efetivo": round(k_ef,4), "x_efetivo": round(x,4),
        "q_entregue": round(q_nec if deficit<=0 else q_ef, 5),
        "P_nec": round(P_nec,2), "deficit": round(deficit,2),
        "bocal_numero": None, "bocal_cor": None, "bocal_orificio_mm": None,
        "bocal_k": k, "bocal_x": x,
        "q_por_bocal_l_h": round(q_nec/n_bocais*1000,1),
        "dentro_da_faixa": True, "regulador_necessario": False, "flags": [],
    }


def calcular_pivo(
    raio_m: float,
    lamina_mm_dia: float,
    horas_dia: float,
    P_entrada_mca: float,
    k_emissor_m3h: float = 0.7,
    x_emissor: float = 0.5,
    espacamento_m: float = 5.0,
    perfil_terreno: Optional[list] = None,
    espacamento_bocais_m: float = 2.5,
    modelo_deflector: Optional[str] = "preto",
    velocidade_percentual: float = 0.0,
    v_max_ultima_torre_m_min: float = 2.2,
) -> dict:

    usa_catalogo = modelo_deflector is not None
    usa_angular  = velocidade_percentual > 0
    v_atual = v_max_ultima_torre_m_min * (velocidade_percentual/100.0) if usa_angular else 0.0
    lam_h   = lamina_mm_dia / horas_dia

    vaos_brutos = _montar_vaos(raio_m)
    raio_real   = sum(v["comp"] for v in vaos_brutos)
    area_m2     = math.pi * raio_real**2
    Q_total_m3h = (lamina_mm_dia / 1000.0 * area_m2) / horas_dia
    Q_m3s       = Q_total_m3h / 3600.0

    v_no_maior_D = Q_m3s / _A(DIAMETROS_PIVO[0]["m"])
    Q_excede     = Q_total_m3h > Q_MAX_10POL_M3H
    Q_alto       = Q_total_m3h > Q_RECOM_MAX_M3H and not Q_excede
    reg_obrig    = P_entrada_mca > P_MAX_BOCAL

    if usa_angular and v_atual > 0:
        circ         = 2.0 * math.pi * raio_real
        t_volta_h    = circ / v_atual / 60.0
        n_voltas_dia = horas_dia / t_volta_h
        lam_volta_mm = lamina_mm_dia / n_voltas_dia
    else:
        t_volta_h = n_voltas_dia = lam_volta_mm = None

    P = P_entrada_mca
    diam_ant_m = DIAMETROS_PIVO[0]["m"]
    trechos, diams, n_vaos_reg = [], {}, 0

    for idx, vao in enumerate(vaos_brutos):
        r0   = round(sum(v["comp"] for v in vaos_brutos[:idx]), 3)
        r1   = round(r0 + vao["comp"], 3)
        L    = vao["comp"]
        r_med = (r0 + r1) / 2.0

        d_info     = _diametro_vao(Q_m3s, diam_ant_m)
        diam_ant_m = d_info["m"]
        D          = d_info["m"]
        v_tubo     = Q_m3s / _A(D) if _A(D) > 0 else 0.0

        hf    = _hw(Q_m3s, D, L)
        dz    = _dz(perfil_terreno or [], r0, r1)
        P_out = max(P - hf - dz, 0.0)
        P_med = (P + P_out) / 2.0
        n_bocais = max(1, round(L / espacamento_bocais_m))

        if usa_angular and lam_volta_mm is not None:
            q_nec      = _q_nec_angular(lam_volta_mm, r_med, raio_real,
                                         v_max_ultima_torre_m_min,
                                         velocidade_percentual, espacamento_bocais_m)
            v_local_mm = v_atual * (r_med/raio_real) if raio_real > 0 else 0
            t_pass_min = espacamento_bocais_m/v_local_mm if v_local_mm > 0 else None
        else:
            q_nec      = _q_nec_continuo(lam_h, r0, r1)
            v_local_mm = None
            t_pass_min = None

        em = _emissor_catalogo(q_nec, P_med, n_bocais,
                                modelo_deflector, P_entrada_mca) if usa_catalogo else None
        if em is None:
            em = _emissor_generico(q_nec, P_med, n_bocais, k_emissor_m3h, x_emissor)

        if em.get("regulador_necessario"): n_vaos_reg += 1

        q_ef    = em["q_entregue"]
        deficit = em["deficit"]
        # lâmina real: usa q_bocal(P_operacao) para refletir o CU real
        # P_operacao = min(P_med, P_MAX_BOCAL) pois o regulador limita a pressão
        P_op = min(P_med, P_MAX_BOCAL) if usa_catalogo else P_med
        k_ef_r = em["k_efetivo"]
        x_ef_r = em["x_efetivo"]
        q_bocal_real = k_ef_r * (P_op ** x_ef_r) if P_op > 0 and k_ef_r > 0 else q_ef
        # se há déficit, já usa q_ef (que é menor que q_nec)
        # se não há déficit, usa q_bocal_real para mostrar CU verdadeiro
        q_para_lam = q_ef if deficit > 0 else q_bocal_real
        lam_dia = _lam_mm_h(q_para_lam, r0, r1) * horas_dia

        at = list(em["flags"])
        if v_tubo > V_MAX:
            at.append(f"CRÍTICO: v={v_tubo:.2f} m/s > {V_MAX} — golpe de aríete")
        elif 0 < v_tubo < V_MIN:
            at.append(f"ALERTA: v={v_tubo:.2f} m/s < {V_MIN} — sedimentação")
        if deficit > 2.0:
            at.append(f"CRÍTICO: déficit {deficit:.1f} mca — "
                      f"lâmina reduzida {round((1-lam_dia/lamina_mm_dia)*100)}%")
        elif deficit > 0.5:
            at.append(f"ALERTA: déficit {deficit:.1f} mca no vão {idx+1}")
        if P_out < P_MIN_FINAL:
            at.append(f"CRÍTICO: P_saída {P_out:.1f} < mínimo ({P_MIN_FINAL} mca)")

        d_mm = round(D * 1000)
        diams.setdefault(d_mm, {"nome": d_info["nome"], "vaos": 0, "comprimento_m": 0.0})
        diams[d_mm]["vaos"]          += 1
        diams[d_mm]["comprimento_m"] += round(L, 2)

        trechos.append({
            "indice": idx+1, "tipo": vao["tipo"],
            "r_ini_m": r0, "r_fim_m": r1, "comprimento_m": round(L,3),
            "balanco": vao.get("balanco", False),
            "diametro_nominal": d_info["nome"], "diametro_mm": d_mm,
            "n_bocais": n_bocais, "k_efetivo": em["k_efetivo"], "x_efetivo": em["x_efetivo"],
            "Q_in_m3h": round(Q_m3s*3600,4), "Q_emit_m3h": round(q_ef,4),
            "Q_out_m3h": round(max(Q_m3s*3600-q_ef,0),4),
            "velocidade_m_s": round(v_tubo,4), "hf_mca": round(hf,4), "dz_mca": round(dz,4),
            "P_in_mca": round(P,3), "P_out_mca": round(P_out,3), "P_media_mca": round(P_med,3),
            "emissor": {
                "n_bocais": n_bocais, "k_efetivo": em["k_efetivo"], "x_efetivo": em["x_efetivo"],
                "posicao_m": round(r_med,2), "area_anel_m2": round(_area_anel(r0,r1),1),
                "q_necessaria_m3h": round(q_nec,4), "q_necessaria_l_h": round(q_nec*1000,1),
                "q_por_bocal_l_h": em["q_por_bocal_l_h"],
                "P_necessaria_mca": em["P_nec"], "P_disponivel_mca": round(P_med,2),
                "deficit_pressao_mca": deficit,
                "q_real_m3h": round(q_ef,4), "q_real_l_h": round(q_ef*1000,1),
                "lamina_real_mm_dia": round(lam_dia,3),
                "desvio_pct": round((lam_dia-lamina_mm_dia)/lamina_mm_dia*100,1)
                              if lamina_mm_dia > 0 else 0,
                "bocal_numero": em["bocal_numero"], "bocal_cor": em["bocal_cor"],
                "bocal_orificio_mm": em["bocal_orificio_mm"],
                "bocal_k": em["bocal_k"], "bocal_x": em["bocal_x"],
                "dentro_da_faixa": em["dentro_da_faixa"],
                "regulador_necessario": em.get("regulador_necessario", False),
                "modelo_deflector": modelo_deflector,
                "v_local_m_min": round(v_local_mm,4) if v_local_mm else None,
                "t_passagem_min": round(t_pass_min,3) if t_pass_min else None,
                "lam_por_volta_mm": round(lam_volta_mm,4) if lam_volta_mm else None,
            },
            "alertas": at if at else None,
        })

        Q_m3s = max(Q_m3s - q_ef/3600.0, 0.0)
        P     = P_out

    lams    = [t["emissor"]["lamina_real_mm_dia"] for t in trechos]
    lam_med = sum(lams)/len(lams) if lams else 0
    cu      = (100*(1-sum(abs(l-lam_med) for l in lams)/(len(lams)*lam_med))
               if lam_med > 0 else 0)
    P_final = trechos[-1]["P_out_mca"] if trechos else 0
    td      = [t for t in trechos if t["emissor"]["deficit_pressao_mca"] > 0.5]
    vels    = [t["velocidade_m_s"] for t in trechos if t["velocidade_m_s"] > 0]

    bocais_usados = {}
    for t in trechos:
        e = t["emissor"]; num = e.get("bocal_numero")
        if num is not None:
            chave = f"#{num}"
            bocais_usados.setdefault(chave, {
                "numero": num, "cor": e.get("bocal_cor","—"),
                "orificio_mm": e.get("bocal_orificio_mm"), "vaos": 0, "total_bocais": 0})
            bocais_usados[chave]["vaos"]         += 1
            bocais_usados[chave]["total_bocais"] += t["n_bocais"]

    alertas = []
    if Q_excede:
        lam_max   = Q_MAX_10POL_M3H * horas_dia / area_m2 * 1000
        horas_min = (lamina_mm_dia/1000*area_m2) / Q_MAX_10POL_M3H
        alertas.append(
            f"CRÍTICO: Vazão {round(Q_total_m3h)} m³/h excede capacidade do 10\" "
            f"({round(Q_MAX_10POL_M3H)} m³/h). "
            f"Reduzir lâmina para ≤{lam_max:.1f} mm/dia OU operar {horas_min:.0f}h/dia."
        )
    elif Q_alto:
        alertas.append(
            f"ALERTA: Vazão {round(Q_total_m3h)} m³/h acima do recomendado "
            f"({Q_RECOM_MAX_M3H:.0f} m³/h). v={v_no_maior_D:.2f} m/s."
        )
    if reg_obrig:
        alertas.append(
            f"CRÍTICO: P={P_entrada_mca:.1f} mca > máximo i-WOB2 ({P_MAX_BOCAL:.1f} mca). "
            f"REGULADORES PSR-2 OBRIGATÓRIOS em todos os {len(trechos)} vãos."
        )
    if P_final < P_MIN_FINAL:
        alertas.append(
            f"CRÍTICO: Pressão final {P_final:.1f} mca insuficiente "
            f"(mínimo {P_MIN_FINAL} mca) — aumentar HMT"
        )
    if td:
        max_def = max(t["emissor"]["deficit_pressao_mca"] for t in td)
        nivel   = "CRÍTICO" if max_def > 3 else "ALERTA"
        alertas.append(
            f"{nivel}: {len(td)} vão(s) ({round(len(td)/len(trechos)*100)}%) "
            f"com déficit — máx. {max_def:.1f} mca"
        )
    if cu < 70:
        alertas.append(f"CRÍTICO: CU={cu:.1f}% muito abaixo do mínimo (70%)")
    elif cu < 80:
        alertas.append(f"ALERTA: CU={cu:.1f}% abaixo do aceitável (80%)")
    if vels and max(vels) > V_MAX:
        alertas.append(f"CRÍTICO: v_max={max(vels):.2f} m/s — golpe de aríete")
    if vels and min(vels) < V_MIN:
        alertas.append(f"ALERTA: v_min={min(vels):.2f} m/s — sedimentação")
    if usa_angular and n_voltas_dia is not None and n_voltas_dia < 0.5:
        alertas.append(
            f"ALERTA: {n_voltas_dia:.2f} volta(s)/dia — pivô não completa 1 volta "
            f"nas {horas_dia:.0f}h. Lâmina/volta={lam_volta_mm:.2f} mm."
        )

    return {
        "trechos": trechos,
        "resumo": {
            "raio_m": raio_m, "raio_real_m": round(raio_real,2),
            "delta_raio_m": round(raio_real-raio_m,2),
            "area_ha": round(area_m2/10000,2),
            "Q_total_m3h": round(Q_total_m3h,3),
            "Q_excede_catalogo": Q_excede, "Q_acima_recomendado": Q_alto,
            "v_primeiro_vao_m_s": round(v_no_maior_D,3),
            "P_entrada_mca": round(P_entrada_mca,2),
            "P_final_mca": round(P_final,2), "pressao_final_ok": P_final >= P_MIN_FINAL,
            "reguladores_obrigatorios": reg_obrig, "n_vaos_com_regulador": n_vaos_reg,
            "lamina_alvo_mm_dia": lamina_mm_dia,
            "lamina_media_mm_dia": round(lam_med,3),
            "lamina_min_mm_dia": round(min(lams) if lams else 0,3),
            "lamina_max_mm_dia": round(max(lams) if lams else 0,3),
            "CU_pct": round(cu,1), "n_trechos": len(trechos),
            "trechos_com_deficit": len(td), "telescopia": diams,
            "bocais_usados": bocais_usados,
            "modelo_deflector": modelo_deflector,
            "usa_catalogo_real": usa_catalogo,
            "modelo_calculo": "angular" if usa_angular else "continuo",
            "velocidade_percentual": velocidade_percentual if usa_angular else None,
            "v_max_ultima_torre_m_min": v_max_ultima_torre_m_min if usa_angular else None,
            "v_atual_m_min": round(v_atual,3) if usa_angular else None,
            "circunferencia_m": round(2*math.pi*raio_real,1) if usa_angular else None,
            "t_volta_h": round(t_volta_h,3) if t_volta_h else None,
            "t_volta_min": round(t_volta_h*60,1) if t_volta_h else None,
            "n_voltas_dia": round(n_voltas_dia,3) if n_voltas_dia else None,
            "lamina_por_volta_mm": round(lam_volta_mm,3) if lam_volta_mm else None,
        },
        "alertas": alertas,
    }
