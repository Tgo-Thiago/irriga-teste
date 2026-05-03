import numpy as np
from core.adutora import calcular_adutora
from core.bomba import calcular_hmt

def gerar_curva_sistema(dados, vazao_projeto):

    pontos = []

    # varre de 50% até 150% da vazão
    for fator in np.linspace(0.5, 1.5, 10):

        Q = vazao_projeto * fator

        # recalcula adutora com nova vazão
        segmentos = [{
            "diametro_interno_m": dados["diametro_adutora_m"],
            "comprimento_m": dados["distancia_captacao_ate_centro"],
            "componentes": []
        }]

        adutora = calcular_adutora(Q, segmentos)

        perdas = adutora["perda_total_mca"]

        hmt = calcular_hmt(
            dados["desnivel_succao"],
            dados["desnivel_recalque"],
            perdas,
            pressao_pivo=dados["pressao_pivo"]
        )

        pontos.append({
            "vazao": Q,
            "hmt": hmt
        })

    return pontos
