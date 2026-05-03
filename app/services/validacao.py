"""
validacao.py — validações completas do projeto.
Compatível com o motor definitivo (Q_excede, reguladores, bocais, angular).
"""


def validar_projeto(res: dict) -> list:
    alertas = []
    pivo    = res.get("pivo", {})
    resumo  = pivo.get("resumo", {})
    adutora = res.get("adutora", {})
    bomba   = res.get("bomba_selecionada") or {}
    trechos = pivo.get("trechos", [])

    usa_catalogo = resumo.get("usa_catalogo_real", False)

    # ── Q excessiva ───────────────────────────────────────────
    if resumo.get("Q_excede_catalogo"):
        Q   = resumo.get("Q_total_m3h", 0)
        lam = resumo.get("lamina_alvo_mm_dia", 0)
        h   = res.get("entrada", {}).get("horas") or 20
        area = resumo.get("area_ha", 1) or 1
        lam_max  = 366 * h / (area * 10000) * 1000
        hora_min = (lam / 1000 * area * 10000) / 366
        alertas.append(
            f"CRÍTICO — Vazão {round(Q)} m³/h excede a capacidade máxima do tubo 10\" "
            f"(366 m³/h). Reduzir lâmina para ≤{lam_max:.1f} mm/dia "
            f"OU operar ≥{hora_min:.0f}h/dia OU dividir em 2 pivôs menores."
        )
    elif resumo.get("Q_acima_recomendado"):
        alertas.append(
            f"ALERTA — Vazão {round(resumo.get('Q_total_m3h',0))} m³/h acima do "
            f"recomendado para 10\" (300 m³/h). Velocidade: "
            f"{resumo.get('v_primeiro_vao_m_s',0):.2f} m/s. "
            f"Monitorar desgaste da tubulação."
        )

    # ── Reguladores obrigatórios ─────────────────────────────
    if resumo.get("reguladores_obrigatorios"):
        P   = resumo.get("P_entrada_mca", 0)
        n   = resumo.get("n_trechos", 0)
        n_r = resumo.get("n_vaos_com_regulador", n)
        alertas.append(
            f"CRÍTICO — Pressão {P:.1f} mca excede o máximo do bocal "
            f"Senninger i-WOB2 (10,5 mca). "
            f"REGULADORES PSR-2 obrigatórios em {n_r} vão(s). "
            f"Incluir na lista de materiais."
        )

    # ── Pressão final ─────────────────────────────────────────
    P_final = resumo.get("P_final_mca", 0)
    if P_final < 4.2:
        alertas.append(
            f"CRÍTICO — Pressão final {P_final:.1f} mca abaixo do mínimo absoluto "
            f"do bocal i-WOB2 (4,2 mca). Sistema inoperante."
        )
    elif P_final < 7.0:
        alertas.append(
            f"ALERTA — Pressão final {P_final:.1f} mca abaixo da pressão ideal "
            f"(7,0 mca). Uniformidade reduzida. Aumentar HMT ou reduzir raio."
        )
    elif P_final < 10.0:
        alertas.append(
            f"ALERTA — Pressão final {P_final:.1f} mca. Usar bocais ≥ #12 e "
            f"espaçamento máx. 3,0 m."
        )

    # ── Déficits de pressão ───────────────────────────────────
    td = [t for t in trechos if t["emissor"]["deficit_pressao_mca"] > 0.5]
    if td:
        max_def  = max(t["emissor"]["deficit_pressao_mca"] for t in td)
        posicoes = [f"{t['r_ini_m']:.0f}–{t['r_fim_m']:.0f}m" for t in td[:3]]
        alertas.append(
            f"Déficit de pressão em {len(td)} vão(s) (máx. {max_def:.1f} mca). "
            f"Primeiros: {', '.join(posicoes)}{'...' if len(td)>3 else ''}."
        )

    # ── Bocais fora da faixa ──────────────────────────────────
    if usa_catalogo:
        fora = [t for t in trechos if t["emissor"].get("dentro_da_faixa") is False]
        if fora:
            alertas.append(
                f"ALERTA — {len(fora)} vão(s) com pressão fora da faixa operacional "
                f"do bocal (4,2–10,5 mca). Instalar reguladores de pressão."
            )
        grandes = [t for t in trechos if (t["emissor"].get("bocal_numero") or 0) > 22]
        if grandes:
            alertas.append(
                f"ATENÇÃO — {len(grandes)} vão(s) com bocais acima de #22 (alta "
                f"taxa de aplicação). Recomendado apenas para solos arenosos ou "
                f"franco-arenosos."
            )

    # ── Velocidades ───────────────────────────────────────────
    vels = [(t["indice"], t["velocidade_m_s"]) for t in trechos if t["velocidade_m_s"] > 0]
    altas  = [(i,v) for i,v in vels if v > 2.0]
    baixas = [(i,v) for i,v in vels if v < 0.5]
    if altas:
        alertas.append(
            f"Velocidade acima de 2,0 m/s em {len(altas)} trecho(s) — "
            f"máx. {max(v for _,v in altas):.2f} m/s. "
            f"Risco de golpe de aríete e desgaste acelerado."
        )
    if baixas:
        alertas.append(
            f"Velocidade abaixo de 0,5 m/s em {len(baixas)} trecho(s). "
            f"Risco de sedimentação e incrustação."
        )

    # ── Uniformidade ─────────────────────────────────────────
    cu = resumo.get("CU_pct", 0)
    if cu < 70:
        alertas.append(
            f"CRÍTICO — CU = {cu:.1f}%. Distribuição muito irregular. "
            f"Revisar pressão de entrada e seleção de bocais."
        )
    elif cu < 80:
        alertas.append(f"CU = {cu:.1f}% abaixo do aceitável (80%). "
                       f"Ajustar pressão no centro do pivô.")
    elif cu < 85:
        alertas.append(f"CU = {cu:.1f}% — uniformidade razoável. Ideal acima de 85%.")

    # ── Modelo angular ────────────────────────────────────────
    n_voltas = resumo.get("n_voltas_dia")
    if n_voltas is not None and n_voltas < 0.5:
        lv = resumo.get("lamina_por_volta_mm", 0)
        alertas.append(
            f"ALERTA — {n_voltas:.2f} volta(s)/dia com velocidade "
            f"{resumo.get('velocidade_percentual',0):.0f}%. "
            f"Pivô não completa 1 volta nas {res.get('entrada',{}).get('horas',0):.0f}h. "
            f"Lâmina/volta = {lv:.2f} mm."
        )

    # ── Adutora ───────────────────────────────────────────────
    vel_adut = adutora.get("velocidade_media_m_s", 0)
    if vel_adut > 2.5:
        alertas.append(f"Velocidade na adutora {vel_adut:.2f} m/s muito alta. "
                       f"Aumentar diâmetro.")
    elif vel_adut > 2.0:
        alertas.append(f"Velocidade na adutora {vel_adut:.2f} m/s elevada. "
                       f"Verificar diâmetro.")
    elif 0 < vel_adut < 0.8:
        alertas.append(f"Velocidade na adutora {vel_adut:.2f} m/s baixa. "
                       f"Risco de sedimentação.")
    hf_adut = adutora.get("perda_total_mca", 0)
    if hf_adut > 15:
        alertas.append(f"Perda de carga na adutora {hf_adut:.1f} mca elevada. "
                       f"Considerar aumentar diâmetro.")

    # ── Bomba ─────────────────────────────────────────────────
    hmt = res.get("hmt_com_margem_m", 0)
    if not bomba or bomba.get("status") == "inexistente":
        alertas.append(
            f"Nenhuma bomba do catálogo atende Q={res.get('vazao_m3h',0):.1f} m³/h "
            f"e HMT={hmt:.1f} m. Solicitar bomba especial ou revisar parâmetros."
        )
    else:
        margem = bomba.get("margem_m", 0)
        if margem < 2:
            alertas.append(f"Bomba com margem de apenas {margem:.1f} m — "
                           f"selecionar modelo de maior porte.")
        elif margem < 5:
            alertas.append(f"Margem da bomba {margem:.1f} m — aceitável mas no limite.")
    if hmt > 100:
        alertas.append(f"HMT = {hmt:.1f} m muito elevada — "
                       f"verificar desníveis e distância de captação.")

    # ── Potência ──────────────────────────────────────────────
    pot = res.get("potencia_bomba_kw", 0)
    if pot > 150:
        alertas.append(f"Potência instalada {pot:.1f} kW elevada — "
                       f"avaliar viabilidade elétrica.")

    # ── Lâmina ────────────────────────────────────────────────
    lam_min  = resumo.get("lamina_min_mm_dia", 0)
    lam_alvo = resumo.get("lamina_alvo_mm_dia", 0)
    if lam_alvo > 0 and lam_min < lam_alvo * 0.85:
        alertas.append(
            f"Lâmina mínima {lam_min:.2f} mm/dia "
            f"({round((1-lam_min/lam_alvo)*100)}% abaixo do alvo). "
            f"Cultura pode sofrer déficit hídrico."
        )

    # propaga alertas do motor sem duplicar
    for a in pivo.get("alertas", []):
        if a not in alertas:
            alertas.append(a)

    return alertas
