# app/core/pivot.py

import math
from app.core.hydraulics import Trecho, Emissor
from app.core.topografia import calcular_delta_z


# =========================================================
# 🔹 NOVO MODELO (OFICIAL)
# =========================================================

def gerar_trechos_pivo(
    vaos,
    espacamento_emissores_m,
    emissor_info,
    perfil_terreno=None
):
    """
    Gera trechos hidráulicos do pivô com múltiplos emissores por trecho.
    Estrutura compatível com cálculo hidráulico detalhado.
    """

    if not vaos:
        return []

    if espacamento_emissores_m <= 0:
        raise ValueError("Espaçamento entre emissores inválido")

    k = emissor_info.get("k")
    x = emissor_info.get("x")

    if k is None or x is None:
        raise ValueError("Parâmetros do emissor (k, x) não informados")

    trechos = []

    for vao in vaos:

        L_total = max(vao.get("comprimento_m", 0), 0)
        if L_total <= 0:
            continue

        D = vao.get("diametro_m", 0.219)

        # número de subdivisões hidráulicas
        n_trechos = max(1, int(L_total / espacamento_emissores_m))
        L_trecho = L_total / n_trechos

        for _ in range(n_trechos):

            # 🔥 múltiplos emissores por trecho (consistente com física)
            n_emissores = max(1, int(L_trecho / espacamento_emissores_m))

            emissores = [
                Emissor(k, x) for _ in range(n_emissores)
            ]

            trecho = Trecho(
                comprimento=L_trecho,
                diametro=D,
                emissores=emissores
            )

            trechos.append(trecho)

    return trechos


# =========================================================
# 🔁 LEGADO (MANTIDO PARA COMPATIBILIDADE)
# =========================================================

def calcular_perfil_pivo(
    vaos,
    vazao_total_m3h,
    pressao_entrada,
    rugosidade=0.000046,
    perfil_terreno=None
):
    """
    ⚠️ Modelo simplificado (LEGADO)
    Mantido apenas para fallback e compatibilidade.

    Não representa fielmente a hidráulica com emissores distribuídos.
    """

    if not vaos:
        return []

    Q_total = max(vazao_total_m3h, 0) / 3600
    total = sum(max(v.get("comprimento_m", 0), 0) for v in vaos)

    if total <= 0:
        return []

    acumulado = 0
    perfil = []
    pressao = max(pressao_entrada, 0)
    pos_anterior = 0

    for vao in vaos:

        L = max(vao.get("comprimento_m", 0), 0)
        if L <= 0:
            continue

        D = max(vao.get("diametro_m", 0.219), 0.001)

        frac = acumulado / total
        Q_local = Q_total * (1 - frac)

        A = math.pi * (D / 2) ** 2
        v = Q_local / A if A > 0 else 0
        v = max(v, 0.3)  # evita velocidade irreal

        # 🔹 perda de carga simplificada
        f = 0.02
        hf = f * (L / D) * (v**2 / (2 * 9.81))

        # mínimo empírico (evita zero hidráulico)
        hf = max(hf, 0.025 * L)

        pos_atual = acumulado + L

        delta_z = calcular_delta_z(
            perfil_terreno,
            pos_anterior,
            pos_atual
        )

        pressao -= (hf + delta_z)
        pressao = max(pressao, 0)

        acumulado += L
        pos_anterior = pos_atual

        perfil.append({
            "posicao_m": round(acumulado, 2),
            "pressao_mca": round(pressao, 2),
            "vazao_m3s": round(Q_local, 4),
            "velocidade_m_s": round(v, 2),
            "delta_z_m": round(delta_z, 3)
        })

    return perfil