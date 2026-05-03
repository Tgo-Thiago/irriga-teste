# ---------------------------------------------

# INTERPOLAÇÃO DE TERRENO

# ---------------------------------------------

def interpolar_cota(perfil_terreno, posicao):


    if not perfil_terreno:
        return 0

    perfil = sorted(perfil_terreno, key=lambda x: x["x"])

    if posicao <= perfil[0]["x"]:
        return perfil[0]["z"]

    if posicao >= perfil[-1]["x"]:
        return perfil[-1]["z"]

    for i in range(len(perfil) - 1):
        p1 = perfil[i]
        p2 = perfil[i + 1]

        if p1["x"] <= posicao <= p2["x"]:
            frac = (posicao - p1["x"]) / (p2["x"] - p1["x"])
            return p1["z"] + frac * (p2["z"] - p1["z"])

    return perfil[-1]["z"]

# ---------------------------------------------
# DELTA DE ELEVAÇÃO
# ---------------------------------------------

def calcular_delta_z(perfil_terreno, pos_anterior, pos_atual):


    z1 = interpolar_cota(perfil_terreno, pos_anterior)
    z2 = interpolar_cota(perfil_terreno, pos_atual)

    return round(z2 - z1, 3)

