from app.core.pivot import calcular_perfil_pivo

# =====================================================
# DIÂMETROS DISPONÍVEIS (m)
# =====================================================

DIAMETROS = [
    0.25,   # 10"
    0.219,  # 8 5/8"
    0.168,  # 6 5/8"
    0.141,  # 5 9/16"
]

# =====================================================
# GERAR COMBINAÇÕES INTELIGENTES
# =====================================================

def gerar_combinacoes(num_vaos):

    combinacoes = []

    for d1 in DIAMETROS:
        for d2 in DIAMETROS:
            for d3 in DIAMETROS:

                # 🔥 regra física obrigatória
                if not (d1 >= d2 >= d3):
                    continue

                combo = []

                for i in range(num_vaos):

                    frac = i / (num_vaos - 1)

                    # 🔥 distribuição REAL de pivô
                    if frac <= 0.5:
                        combo.append(d1)   # início
                    elif frac <= 0.8:
                        combo.append(d2)   # meio
                    else:
                        combo.append(d3)   # final

                combinacoes.append(combo)

    return combinacoes


# =====================================================
# SCORE HIDRÁULICO
# =====================================================

def avaliar_configuracao(perfil, diametros):

    velocidades = [
        p.get("velocidade_m_s", 0)
        for p in perfil if p.get("velocidade_m_s") is not None
    ]

    if not velocidades:
        return float("inf")

    v_min = min(velocidades)
    v_max = max(velocidades)

    score = 0

    # ---------------- VELOCIDADE ----------------
    if v_min < 0.6:
        score += 200
    elif v_min < 0.8:
        score += 80
    elif v_min < 1.0:
        score += 20

    if v_max > 2.5:
        score += 150
    elif v_max > 2.2:
        score += 60

    # ---------------- ESTABILIDADE ----------------
    score += (v_max - v_min) * 50

    # ---------------- CUSTO ----------------
    score += sum(diametros) * 10

    # ---------------- TRANSIÇÕES ----------------
    transicoes = sum(
        1 for i in range(1, len(diametros))
        if diametros[i] != diametros[i - 1]
    )

    score += transicoes * 15

    return score


# =====================================================
# OTIMIZAÇÃO PRINCIPAL
# =====================================================

def nome_diametro(d):
    if abs(d - 0.254) < 0.001:
        return '10"'
    elif abs(d - 0.219) < 0.001:
        return '8 5/8"'
    elif abs(d - 0.168) < 0.001:
        return '6 5/8"'
    else:
        return f"{round(d*1000)} mm"


def otimizar_diametros(vaos, vazao, pressao):

    melhor = None
    melhor_score = float("inf")

    combinacoes = gerar_combinacoes(len(vaos))

    for combo in combinacoes[:40]:

        vaos_testados = []

        for i, vao in enumerate(vaos):

            diam_m = combo[i]

            vaos_testados.append({
                "tipo": vao["tipo"],
                "comprimento_m": vao["comprimento_m"],

                "diametro_m": diam_m,
                "diametro_mm": round(diam_m * 1000),
                "diametro_nominal": nome_diametro(diam_m)
            })

        try:
            perfil = calcular_perfil_pivo(
                vaos_testados,
                vazao,
                pressao
            )
        except Exception:
            continue

        score = avaliar_configuracao(perfil, combo)

        if score < melhor_score:
            melhor_score = score
            melhor = vaos_testados

    # 🔥 fallback seguro (telescopia real)
    if not melhor:
        melhor = []

        n = len(vaos)

        for i, vao in enumerate(vaos):

            frac = i / (n - 1) if n > 1 else 0

            if frac <= 0.5:
                diam = 0.254   # 10"
            elif frac <= 0.8:
                diam = 0.219   # 8 5/8"
            else:
                diam = 0.168   # 6 5/8"

            melhor.append({
                "tipo": vao["tipo"],
                "comprimento_m": vao["comprimento_m"],
                "diametro_m": diam,
                "diametro_mm": round(diam * 1000),
                "diametro_nominal": nome_diametro(diam)
            })

    return melhor