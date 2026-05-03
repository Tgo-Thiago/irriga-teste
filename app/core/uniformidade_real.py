import math

# --------------------------------------------------

# CÁLCULO DA LÂMINA POR ANEL (CORRETO PARA PIVÔ)

# --------------------------------------------------

def calcular_laminas(emissores):


    if not emissores:
        return []

    laminas = []

    r_anterior = 0

    for e in emissores:

        r_atual = e["posicao_m"]
        q = e["vazao_m3h"]

        # -----------------------------------------
        # ÁREA DO ANEL (m²)
        # -----------------------------------------
        area_anel = math.pi * (r_atual**2 - r_anterior**2)

        if area_anel <= 0:
            lamina = 0
        else:
            # m³/h → mm/h
            lamina = (q / area_anel) * 1000

        laminas.append({
            "posicao_m": r_atual,
            "lamina_mm_h": lamina
        })

        r_anterior = r_atual

    return laminas


# --------------------------------------------------   
# UNIFORMIDADE REAL (BASEADA NA LÂMINA)
# --------------------------------------------------

def calcular_uniformidade_real(laminas):


    if not laminas:
        return {
            "cu_real": 0,
            "du_real": 0,
            "lamina_media_mm_h": 0
        }

    # -----------------------------------------
    # PONDERAÇÃO POR ÁREA
    # -----------------------------------------
    valores = []
    pesos = []

    r_anterior = 0

    for l in laminas:
        r = l["posicao_m"]
        lam = l["lamina_mm_h"]

        area = math.pi * (r**2 - r_anterior**2)

        valores.append(lam)
        pesos.append(area)

        r_anterior = r

    # média ponderada
    soma_pesos = sum(pesos)
    media = sum(v * p for v, p in zip(valores, pesos)) / soma_pesos if soma_pesos > 0 else 0

    # -----------------------------------------
    # CU PONDERADO
    # -----------------------------------------
    desvios = [abs(v - media) * p for v, p in zip(valores, pesos)]

    cu = 100 * (1 - sum(desvios) / (soma_pesos * media)) if media > 0 else 0

    # -----------------------------------------
    # DU PONDERADO (quartil inferior por área)
    # -----------------------------------------
    pares = list(zip(valores, pesos))
    pares.sort(key=lambda x: x[0])  # menor lâmina primeiro

    acumulado = 0
    limite = soma_pesos * 0.25

    soma_baixa = 0
    peso_baixa = 0

    for v, p in pares:
        if acumulado >= limite:
          break

        soma_baixa += v * p
        peso_baixa += p
        acumulado += p

    media_baixa = soma_baixa / peso_baixa if peso_baixa > 0 else 0

    du = (media_baixa / media) * 100 if media > 0 else 0

    return {
        "cu_real": round(max(0, cu), 2),
        "du_real": round(max(0, du), 2),
        "lamina_media_mm_h": round(media, 2)
    }

