"""
sugestoes.py — sugestões técnicas e cenários de otimização.
Compatível com motor definitivo (Q_excede, reguladores, angular).
"""

import math


def gerar_sugestoes(res: dict) -> list:
    sugestoes = []
    pivo    = res.get("pivo", {})
    resumo  = pivo.get("resumo", {})
    dados   = res.get("entrada", {})
    bomba   = res.get("bomba_selecionada") or {}
    adutora = res.get("adutora", {})

    Q        = res.get("vazao_m3h", 0)
    hmt      = res.get("hmt_com_margem_m", 0)
    potencia = res.get("potencia_bomba_kw", 0)
    cu       = resumo.get("CU_pct", 0)
    P_final  = resumo.get("P_final_mca", 0)
    P_ent    = resumo.get("P_entrada_mca", 0)
    raio     = resumo.get("raio_real_m", 0)
    area     = resumo.get("area_ha", 0) or 1
    lam_alvo = resumo.get("lamina_alvo_mm_dia", 0)
    horas    = dados.get("horas") or dados.get("horas_trabalho_dia") or 20
    dist     = dados.get("distancia_captacao_ate_centro", 100)
    hf_adut  = adutora.get("perda_total_mca", 0)
    td       = [t for t in pivo.get("trechos",[]) if t["emissor"]["deficit_pressao_mca"]>0.5]
    Q_excede = resumo.get("Q_excede_catalogo", False)
    reg_obrig= resumo.get("reguladores_obrigatorios", False)
    n_voltas = resumo.get("n_voltas_dia")
    lam_volta= resumo.get("lamina_por_volta_mm")

    # ── 1. Q excessiva (mais urgente) ─────────────────────────
    if Q_excede:
        lam_max  = 366 * horas / (area * 10000) * 1000
        raio_max = math.sqrt(366 * horas / (lam_alvo / 1000) / math.pi) if lam_alvo > 0 else 0
        sugestoes.append({
            "tipo": "critico", "prioridade": "critica",
            "mensagem": f"Vazão {round(Q)} m³/h inviável para tubo 10\" — projeto precisa ser redimensionado",
            "acoes": [
                f"Opção 1: Reduzir lâmina para {lam_max:.1f} mm/dia (Q=366 m³/h no limite)",
                f"Opção 2: Reduzir raio para {raio_max:.0f} m (≈{math.pi*raio_max**2/10000:.1f} ha)",
                "Opção 3: Dividir em 2 pivôs menores com captação independente",
            ],
            "impacto_estimado": "Indispensável para viabilizar o projeto",
        })

    # ── 2. Pressão insuficiente / déficit ─────────────────────
    if td and not Q_excede:
        deficit_med = sum(t["emissor"]["deficit_pressao_mca"] for t in td)/len(td)
        delta_P = max(5, round(15 - P_final + deficit_med, 1))
        sugestoes.append({
            "tipo": "pressao", "prioridade": "critica",
            "mensagem": "Pressão insuficiente nos vãos externos",
            "acoes": [
                f"Aumentar pressão de entrada em {delta_P} mca (novo HMT ≈ {hmt+delta_P:.0f} m)",
                "Verificar se a bomba selecionada comporta esse aumento",
                "Reduzir o raio do pivô para diminuir a perda de carga total",
            ],
            "impacto_estimado": f"Elimina déficit em {len(td)} vão(s) — lâmina uniforme",
        })

    # ── 3. Reguladores (quando obrigatórios, sugere modelo) ───
    if reg_obrig:
        n_reg = resumo.get("n_vaos_com_regulador", resumo.get("n_trechos", 0))
        total_boc = sum(t.get("n_bocais", 0) for t in pivo.get("trechos",[]))
        sugestoes.append({
            "tipo": "regulador", "prioridade": "critica",
            "mensagem": f"Reguladores de pressão obrigatórios — {total_boc} unidades PSR-2",
            "acoes": [
                f"Incluir {total_boc}× Senninger PSR-2 (ou equivalente) na lista de materiais",
                "Instalar no topo de cada pendural, acima do bocal",
                f"Regulador ajustado para 7,0 mca (pressão ideal do i-WOB2)",
                "Verificar disponibilidade com o distribuidor antes de fechar o pedido",
            ],
            "impacto_estimado": f"Pressão nos bocais controlada a 7.0 mca — máxima uniformidade",
        })

    # ── 4. CU baixo ───────────────────────────────────────────
    if cu < 80 and not Q_excede:
        sugestoes.append({
            "tipo": "uniformidade", "prioridade": "alta",
            "mensagem": f"CU {cu:.1f}% abaixo do mínimo agronômico (80%)",
            "acoes": [
                "Aumentar pressão no centro do pivô em 3–5 mca",
                "Revisar bocais dos vãos externos (substituir por maior)",
                "Reduzir espaçamento entre emissores para distribuição mais uniforme",
            ],
            "impacto_estimado": "CU esperado > 85% com ajuste de pressão",
        })

    # ── 5. HMT elevada ────────────────────────────────────────
    if hmt > 80:
        sugestoes.append({
            "tipo": "energia", "prioridade": "media",
            "mensagem": f"HMT = {hmt:.1f} m elevada — alto custo energético",
            "acoes": [
                f"Reduzir pressão do pivô de {P_ent} para {max(P_ent-5,15)} mca "
                f"(economia ≈ {round(potencia*0.12):.0f} kW)",
                f"Aumentar diâmetro da adutora (perda atual: {hf_adut:.1f} mca)",
                "Avaliar captação mais próxima para reduzir comprimento da adutora",
            ],
            "impacto_estimado": "Redução de até 15% no consumo energético",
        })

    # ── 6. Bomba não encontrada ───────────────────────────────
    if not bomba or bomba.get("status") == "inexistente":
        sugestoes.append({
            "tipo": "bomba", "prioridade": "critica",
            "mensagem": "Ponto de operação fora do catálogo disponível",
            "acoes": [
                f"Solicitar proposta de bomba: Q={Q:.0f} m³/h, HMT={hmt:.0f} m",
                "Avaliar bomba em série (2 bombas) para HMT elevada",
                "Considerar redução do raio do pivô para diminuir Q necessária",
            ],
            "impacto_estimado": "Indispensável para viabilizar o projeto",
        })

    # ── 7. Operacional: horas ─────────────────────────────────
    if horas > 0 and lam_alvo > 0 and horas < 22 and not Q_excede:
        lam_nova = lam_alvo * (horas / (horas - 2))
        sugestoes.append({
            "tipo": "operacional", "prioridade": "baixa",
            "mensagem": "Aumentar lâmina sem trocar bomba",
            "acoes": [
                f"Reduzir de {horas:.0f}h para {horas-2:.0f}h/dia → lâmina sobe de "
                f"{lam_alvo} para {lam_nova:.1f} mm/dia com a mesma bomba",
                "Verificar se a cultura tolera irrigação mais concentrada",
                "Monitorar umidade do solo para evitar excesso",
            ],
            "impacto_estimado": f"Lâmina aumenta {round((lam_nova/lam_alvo-1)*100)}% sem custo adicional",
        })

    # ── 8. Energia: horário de ponta ──────────────────────────
    if potencia > 50:
        tar_p, tar_fp = 0.85, 0.40
        hp, hfp = min(horas, 4), horas - min(horas, 4)
        custo_at = (potencia*hp*tar_p + potencia*hfp*tar_fp) * 30
        custo_fp = potencia * horas * tar_fp * 30
        economia = custo_at - custo_fp
        sugestoes.append({
            "tipo": "energia", "prioridade": "baixa",
            "mensagem": "Economia com operação fora do horário de ponta",
            "acoes": [
                "Concentrar operação fora do horário de ponta (18h–21h)",
                f"Economia estimada: R$ {economia:.0f}/mês apenas na tarifa",
                "Verificar com a concessionária local o horário de ponta",
            ],
            "impacto_estimado": f"Economia de até R$ {economia:.0f}/mês",
        })

    # ── 9. Adutora ────────────────────────────────────────────
    if hf_adut > 10:
        sugestoes.append({
            "tipo": "adutora", "prioridade": "media",
            "mensagem": f"Perda de carga na adutora {hf_adut:.1f} mca — potencial de melhoria",
            "acoes": [
                "Aumentar diâmetro da adutora um degrau",
                f"Distância atual {dist}m — verificar traçado mais direto",
                "Reduzir número de curvas e conexões",
            ],
            "impacto_estimado": f"Redução de {round(hf_adut*0.4):.0f} mca → HMT menor → bomba menor",
        })

    # ── 10. Modelo angular: aviso de voltas incompletas ───────
    if n_voltas is not None and n_voltas < 1.0:
        sugestoes.append({
            "tipo": "operacional", "prioridade": "media",
            "mensagem": f"Pivô completa apenas {n_voltas:.2f} volta(s)/dia — verificar lâmina acumulada",
            "acoes": [
                f"Lâmina por volta = {lam_volta:.2f} mm — verificar se a cultura suporta",
                "Considerar aumentar a velocidade percentual para mais voltas/dia",
                "Avaliar irrigação em dias alternados com lâmina maior por volta",
            ],
            "impacto_estimado": "Uniformidade de aplicação ao longo do ciclo da cultura",
        })

    # ── 11. Configuração ideal ────────────────────────────────
    sugestoes.append({
        "tipo": "configuracao_ideal", "prioridade": "informativo",
        "mensagem": "Configuração ideal estimada para este sistema",
        "parametros": {
            "pressao_pivo_recomendada_mca": round(max(P_ent, P_final + 5), 1),
            "hmt_recomendada_m":            round(hmt * 1.05, 1),
            "diametro_adutora_recomendado": res.get("diametro_adutora", {}).get("nome", "—"),
            "horas_operacao_otimas_h":      min(horas + 2, 22) if cu < 80 else horas,
            "cu_esperado_pct":              min(round(cu + 8), 95),
        },
        "acoes": [
            "Adotar os parâmetros acima como referência para o projeto executivo",
            "Solicitar cotação de bomba com estas especificações ao fabricante",
            "Validar em campo após a implantação com medidor de pressão portátil",
        ],
        "impacto_estimado": "Projeto otimizado para máxima uniformidade e mínimo custo",
    })

    return sugestoes
