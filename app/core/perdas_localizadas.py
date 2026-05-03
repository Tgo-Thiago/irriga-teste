# Coeficientes K de referência (engenharia hidráulica)
K_COMPONENTES = {
    "entrada": 0.5,
    "saida": 1.0,
    "curva_90": 0.9,
    "curva_45": 0.4,
    "valvula_gaveta_aberta": 0.2,
    "valvula_gaveta_parcial": 5.0,
    "valvula_retencao": 2.5,
    "filtro": 2.0,
    "te_passagem": 0.6,
}

def calcular_perdas_localizadas(velocidade, componentes):
    """
    BUG CORRIGIDO: o código original ignorava o parâmetro 'componentes'
    e usava uma lista hardcoded interna, descartando tudo que era passado.
    Agora usa os componentes recebidos corretamente.
    Também corrigido: hf deve ser calculado DEPOIS de somar todos os K,
    não dentro do loop (acumulava K incorretamente a cada iteração).
    """
    g = 9.81
    K_total = 0.0

    for comp in componentes:
        tipo = comp.get("tipo", "")
        qtd = comp.get("quantidade", 1)
        K = K_COMPONENTES.get(tipo, 0.0)
        K_total += K * qtd

    hf = K_total * (velocidade ** 2) / (2 * g)

    return round(hf, 4), round(K_total, 3)
