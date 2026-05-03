from core.hydraulics import GRAVIDADE

def calcular_hmt(
    desnivel_succao,
    desnivel_recalque,
    perdas,
    perdas_localizadas=0,
    reserva=5,
    pressao_pivo=25
):
    return (
        desnivel_succao +
        desnivel_recalque +
        perdas +
        perdas_localizadas +
        reserva +
        pressao_pivo
    )


def calcular_potencia(vazao_m3h, hmt, eficiencia):
    Q = vazao_m3h / 3600
    P = (1000 * GRAVIDADE * Q * hmt) / eficiencia
    return round(P / 1000, 2)
