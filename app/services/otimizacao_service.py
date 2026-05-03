from services.dimensionamento_service import dimensionar


# =====================================================
# SCORE DE ENGENHARIA (NÍVEL PROFISSIONAL)
# =====================================================

def avaliar_resultado(resultado):

    # -------------------------------------------------
    # REGRAS ELIMINATÓRIAS (CRÍTICO)
    # -------------------------------------------------
    bomba = resultado.get("bomba_selecionada", {})

    if not bomba or bomba.get("status") == "inexistente":
        return float("inf")

    v_min = resultado.get("velocidade_min_m_s", 0)
    v_max = resultado.get("velocidade_max_m_s", 0)

    if v_min < 0.5:
        return float("inf")

    if v_max > 3.0:
        return float("inf")

    # -------------------------------------------------
    # SCORE
    # -------------------------------------------------
    score = 0

    # 🔥 ENERGIA (peso forte)
    potencia = resultado.get("potencia_bomba_kw", 0)
    score += potencia * 1.5

    # 🔥 HMT
    hmt = resultado.get("hmt_com_margem_m", 0)
    score += hmt * 0.8

    # 🔥 ESTABILIDADE HIDRÁULICA
    score += (v_max - v_min) * 25

    # 🔥 UNIFORMIDADE (bônus)
    cu = resultado.get("uniformidade", {}).get("cu_percent", 0)
    score -= cu * 0.6

    # 🔥 MARGEM DE BOMBA
    margem = bomba.get("margem_m", 0)
    if margem < 3:
        score += 50
    elif margem < 5:
        score += 20

    return score


# =====================================================
# GERAÇÃO DE CENÁRIOS (EXPANDIDO)
# =====================================================

def gerar_cenarios(dados_entrada):

    horas_opcoes = [24, 22, 20, 18, 16, 14, 12]
    pressao_opcoes = [15, 20, 25, 30]

    cenarios = []

    for h in horas_opcoes:
        for p in pressao_opcoes:
            cenarios.append({
                "horas_trabalho_dia": h,
                "pressao_pivo_mca": p
            })

    return cenarios


# =====================================================
# OTIMIZAÇÃO PRINCIPAL (NÍVEL AVANÇADO)
# =====================================================

def otimizar_projeto(dados_entrada):

    melhor = None
    melhor_score = float("inf")
    resultados_validos = []

    cenarios = gerar_cenarios(dados_entrada)

    for c in cenarios:

        dados = dados_entrada.copy()
        dados.update(c)

        try:
            resultado = dimensionar(dados)

            score = avaliar_resultado(resultado)

            # 🔥 ignora inviáveis
            if score == float("inf"):
                continue

            registro = {
                "score": round(score, 2),
                "configuracao": c,
                "resultado": resultado
            }

            resultados_validos.append(registro)

            if score < melhor_score:
                melhor_score = score
                melhor = registro

        except Exception:
            continue

    # -------------------------------------------------
    # ORDENA RESULTADOS
    # -------------------------------------------------
    resultados_ordenados = sorted(
        resultados_validos,
        key=lambda x: x["score"]
    )

    # -------------------------------------------------
    # DIAGNÓSTICO
    # -------------------------------------------------
    diagnostico = ""

    if not melhor:
        diagnostico = "Nenhuma configuração viável encontrada"
    else:
        if melhor_score < 80:
            diagnostico = "Projeto otimizado de alta eficiência"
        elif melhor_score < 150:
            diagnostico = "Projeto eficiente com bom desempenho"
        elif melhor_score < 250:
            diagnostico = "Projeto viável com limitações"
        else:
            diagnostico = "Projeto com baixa eficiência energética"

    return {
        "melhor_resultado": melhor,
        "top_5": resultados_ordenados[:5],
        "total_validos": len(resultados_validos),
        "total_testados": len(cenarios),
        "diagnostico": diagnostico
    }
