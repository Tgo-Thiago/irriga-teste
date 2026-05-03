import math

GRAVIDADE = 9.81


# =========================================================
# DARCY-WEISBACH (adutora)
# =========================================================

def perda_darcy(L, D, v, rugosidade=0.000046):
    if D <= 0 or v <= 0:
        return 0, 0, 0

    Re = (v * D) / 1e-6

    try:
        f = 0.25 / (math.log10(
            (rugosidade / (3.7 * D)) + (5.74 / (Re ** 0.9))
        ) ** 2)
    except:
        f = 0.02

    hf = f * (L / D) * (v ** 2 / (2 * GRAVIDADE))
    return hf, f, Re


# =========================================================
# HAZEN-WILLIAMS  Q em m³/s, D em m, L em m → hf em m
# =========================================================

def perda_carga_hazen_williams(Q_m3s, D, L, C=140):
    """
    BUG CORRIGIDO: a fórmula H-W clássica exige Q em m³/s.
    Antes recebia m³/s mas a constante 10.67 é para m³/s.
    J = 10.67 * L * Q^1.852 / (C^1.852 * D^4.87)  [tudo SI]
    """
    if Q_m3s <= 0 or D <= 0:
        return 0
    return 10.67 * L * (Q_m3s ** 1.852) / ((C ** 1.852) * (D ** 4.87))


def velocidade(Q_m3s, D):
    if D <= 0:
        return 0
    area = math.pi * (D ** 2) / 4
    return Q_m3s / area


# =========================================================
# MODELOS
# =========================================================

class Emissor:
    """
    BUG CORRIGIDO: k é fornecido em m³/h na tabela de emissores.
    vazao() devolve m³/s — divide por 3600 UMA SÓ VEZ aqui.
    """
    def __init__(self, k_m3h, x):
        self.k = k_m3h   # m³/h
        self.x = x

    def vazao(self, pressao_mca):
        if pressao_mca <= 0:
            return 0
        # q = k * P^x  →  resultado em m³/h  →  converte para m³/s
        return (self.k * (pressao_mca ** self.x)) / 3600


class Trecho:
    def __init__(self, comprimento, diametro, emissores):
        self.L = comprimento
        self.D = diametro
        self.emissores = emissores

        self.Q_in = 0.0
        self.Q_out = 0.0
        self.pressao_in = 0.0
        self.pressao_out = 0.0
        self.perda = 0.0
        self.velocidade = 0.0
        self.vazao_emitida = 0.0
        self.pressao_media = 0.0


# =========================================================
# SIMULAÇÃO DE UMA PASSAGEM
# =========================================================

def simular_linha(trechos, pressao_inicial):
    P = pressao_inicial

    for trecho in trechos:
        trecho.pressao_in = P

        # --- sem vazão entrando → trecho morto ---
        if trecho.Q_in <= 1e-9:
            trecho.Q_out = 0.0
            trecho.perda = 0.0
            trecho.pressao_out = P
            trecho.velocidade = 0.0
            trecho.pressao_media = P
            trecho.vazao_emitida = 0.0
            continue

        # --- emissores ---
        Q_emit = 0.0
        for emissor in trecho.emissores:
            q_e = emissor.vazao(P)
            q_e = max(q_e, 0.0)
            Q_emit += q_e

        # emissores não podem drenar mais do que entra
        Q_emit = min(Q_emit, trecho.Q_in)
        trecho.vazao_emitida = Q_emit
        trecho.Q_out = max(trecho.Q_in - Q_emit, 0.0)

        # --- perda de carga (H-W) ---
        hf = perda_carga_hazen_williams(trecho.Q_in, trecho.D, trecho.L)
        trecho.perda = hf
        trecho.pressao_out = max(P - hf, 0.0)
        trecho.velocidade = velocidade(trecho.Q_in, trecho.D)
        trecho.pressao_media = (trecho.pressao_in + trecho.pressao_out) / 2

        P = trecho.pressao_out

    return trechos


# =========================================================
# SOLVER ITERATIVO
# =========================================================

def resolver_sistema(trechos, pressao_inicial, vazao_inicial, tol=1e-4, max_iter=50):
    """
    BUG CORRIGIDO: vazao_inicial já chega em m³/h — converte uma vez.
    Loop ajusta Q_in do primeiro trecho até a soma emitida convergir.
    """
    Q = max(vazao_inicial / 3600, 1e-6)   # m³/s

    for _ in range(max_iter):

        trechos[0].Q_in = Q
        for i in range(1, len(trechos)):
            trechos[i].Q_in = trechos[i - 1].Q_out

        simular_linha(trechos, pressao_inicial)

        Q_emit_total = sum(t.vazao_emitida for t in trechos)

        if Q_emit_total < 1e-9:
            break

        erro = abs(Q_emit_total - Q)
        if erro < tol:
            break

        # ajuste proporcional amortecido
        if Q_emit_total > 1e-9:
            fator = Q_emit_total / Q
            fator = max(0.8, min(1.2, fator))
            Q = Q / fator

        Q = max(1e-6, min(Q, 1.0))   # máximo 3600 m³/h — seguro

    return trechos


# =========================================================
# SAÍDA
# =========================================================

def gerar_resultado(trechos):
    resultado = {
        "trechos": [],
        "resumo": {
            "vazao_total_m3s": 0.0,
            "pressao_min": float("inf"),
            "pressao_max": 0.0,
        }
    }

    for i, t in enumerate(trechos):
        resultado["trechos"].append({
            "index": i,
            "pressao_in": round(t.pressao_in, 3),
            "pressao_out": round(t.pressao_out, 3),
            "pressao_media": round(t.pressao_media, 3),
            "vazao_in_m3s": round(t.Q_in, 6),
            "vazao_out_m3s": round(t.Q_out, 6),
            "vazao_emitida_m3s": round(t.vazao_emitida, 6),
            "velocidade": round(t.velocidade, 3),
            "perda_carga": round(t.perda, 4),
        })

        resultado["resumo"]["vazao_total_m3s"] += t.vazao_emitida

        if t.pressao_in > 0:
            resultado["resumo"]["pressao_min"] = min(
                resultado["resumo"]["pressao_min"], t.pressao_in
            )
        resultado["resumo"]["pressao_max"] = max(
            resultado["resumo"]["pressao_max"], t.pressao_in
        )

    if resultado["resumo"]["pressao_min"] == float("inf"):
        resultado["resumo"]["pressao_min"] = 0.0

    return resultado
