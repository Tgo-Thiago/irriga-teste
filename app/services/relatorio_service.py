"""
relatorio_service.py — PDF técnico completo do pivô central.
Todas as leituras do resumo usam as chaves canônicas do motor_pivo.py.
"""

import math
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

COR_HEADER   = colors.HexColor("#1a2f4e")
COR_SUB      = colors.HexColor("#2f6690")
COR_VERDE    = colors.HexColor("#1d6b2e")
COR_VERMELHO = colors.HexColor("#8b0000")
COR_LARANJA  = colors.HexColor("#7a3a00")
COR_LINHA_A  = colors.HexColor("#f5f8fa")
COR_CRITICO  = colors.HexColor("#fde8e8")
COR_ALERTA   = colors.HexColor("#fff8e1")
COR_OK       = colors.HexColor("#e8f5e9")


def _st():
    s = getSampleStyleSheet()
    return {
        "titulo":    ParagraphStyle("T",  fontSize=16, fontName="Helvetica-Bold",
                                    textColor=COR_HEADER, alignment=TA_CENTER, spaceAfter=4),
        "sub":       ParagraphStyle("S",  fontSize=10, fontName="Helvetica",
                                    textColor=COR_SUB, alignment=TA_CENTER, spaceAfter=2),
        "h2":        ParagraphStyle("H2", fontSize=12, fontName="Helvetica-Bold",
                                    textColor=COR_HEADER, spaceBefore=10, spaceAfter=4),
        "h3":        ParagraphStyle("H3", fontSize=10, fontName="Helvetica-Bold",
                                    textColor=COR_SUB, spaceBefore=6, spaceAfter=3),
        "normal":    ParagraphStyle("N",  fontSize=9,  fontName="Helvetica",
                                    spaceAfter=2, leading=13),
        "critico":   ParagraphStyle("CR", fontSize=9,  fontName="Helvetica-Bold",
                                    textColor=COR_VERMELHO, spaceAfter=3),
        "alerta":    ParagraphStyle("AL", fontSize=9,  fontName="Helvetica",
                                    textColor=COR_LARANJA, spaceAfter=3),
        "ok":        ParagraphStyle("OK", fontSize=9,  fontName="Helvetica",
                                    textColor=COR_VERDE, spaceAfter=3),
        "mini":      ParagraphStyle("MI", fontSize=8,  fontName="Helvetica",
                                    textColor=colors.HexColor("#555555")),
    }


def _tab(dados, ws=None, hbg=COR_HEADER):
    t = Table(dados, colWidths=ws, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), hbg),
        ("TEXTCOLOR",     (0,0),(-1,0), colors.white),
        ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 8),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, COR_LINHA_A]),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
    ]))
    return t


def _hr(el):
    el.append(HRFlowable(width="100%", thickness=0.5,
                          color=colors.HexColor("#cccccc"), spaceAfter=6))

def _p(el, txt, st): el.append(Paragraph(str(txt), st))
def _sp(el, h=6):    el.append(Spacer(1, h))


# ── helper: lê resumo do pivo com fallbacks ───────────────────
def _resumo(res):
    return res.get("pivo", {}).get("resumo", {})


# ─────────────────────────────────────────────────────────────
# SEÇÕES
# ─────────────────────────────────────────────────────────────

def _capa(el, st, res, ent):
    _p(el, "RELATÓRIO TÉCNICO DE IRRIGAÇÃO", st["titulo"])
    _p(el, "Sistema de Irrigação por Pivô Central", st["sub"])
    _p(el, f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", st["sub"])
    _sp(el, 10); _hr(el)

    r = _resumo(res)
    dados = [
        ["Parâmetro", "Valor"],
        ["Raio desejado",       f"{r.get('raio_m', ent.get('raio_m', 0)):.1f} m"],
        ["Raio real (vãos)",    f"{r.get('raio_real_m', r.get('raio_m', 0)):.2f} m"],
        ["Área irrigada",       f"{r.get('area_ha', res.get('area_ha', 0)):.2f} ha"],
        ["Lâmina de projeto",   f"{r.get('lamina_alvo_mm_dia', ent.get('lamina_mm_dia', 0))} mm/dia"],
        ["Horas de operação",   f"{ent.get('horas') or ent.get('horas_trabalho_dia', 0)} h/dia"],
        ["Vazão total",         f"{res.get('vazao_m3h', r.get('Q_total_m3h', 0)):.1f} m³/h"],
        ["HMT (com margem)",    f"{res.get('hmt_com_margem_m', 0):.1f} m"],
        ["Potência instalada",  f"{res.get('potencia_bomba_kw', 0):.1f} kW"],
        ["CU (uniformidade)",   f"{r.get('CU_pct', 0):.1f}%"],
    ]
    el.append(_tab(dados, ws=[9*cm, 8*cm])); _sp(el, 8)


def _resumo_exec(el, st, res):
    _p(el, "1. RESUMO EXECUTIVO", st["h2"]); _hr(el)
    r       = _resumo(res)
    alertas = res.get("alertas", [])
    n_crit  = sum(1 for a in alertas if "CRÍTICO" in a.upper())
    n_alert = len(alertas) - n_crit
    ok_p    = r.get("pressao_final_ok", False)
    criticos_h = [a for a in alertas
                   if "CRÍTICO" in a.upper()
                   and "REGULADOR" not in a.upper()
                   and "PSR" not in a.upper()]
    so_reg  = (n_crit > 0 and len(criticos_h) == 0)
    if criticos_h or (n_crit > 0 and not so_reg) or not ok_p:
        status = "REPROVADO"
    elif so_reg:
        status = "APROVADO C/ RESSALVAS"
    else:
        status = "APROVADO"

    dados = [
        ["Indicador", "Valor", "Status"],
        ["Raio real do pivô",
         f"{r.get('raio_real_m', r.get('raio_m', 0)):.2f} m", "—"],
        ["Pressão final",
         f"{r.get('P_final_mca', 0):.1f} mca",
         "OK" if ok_p else "INSUFICIENTE"],
        ["Uniformidade (CU)",
         f"{r.get('CU_pct', 0):.1f}%",
         "OK" if r.get('CU_pct', 0) >= 80 else "BAIXO"],
        ["Trechos c/ déficit",
         f"{r.get('trechos_com_deficit', 0)}/{r.get('n_trechos', 0)}",
         "OK" if r.get('trechos_com_deficit', 0) == 0 else "ATENÇÃO"],
        ["Lâmina alvo",
         f"{r.get('lamina_alvo_mm_dia', 0):.1f} mm/dia", "—"],
        ["Lâmina média aplicada",
         f"{r.get('lamina_media_mm_dia', 0):.2f} mm/dia",
         "OK" if abs(r.get('lamina_media_mm_dia',0) - r.get('lamina_alvo_mm_dia',0)) < 0.5 else "DESVIO"],
        ["Lâmina mínima",
         f"{r.get('lamina_min_mm_dia', 0):.2f} mm/dia",
         "OK" if r.get('lamina_min_mm_dia',0) >= r.get('lamina_alvo_mm_dia',0)*0.9 else "BAIXA"],
        ["Alertas críticos",  str(n_crit),  "OK" if n_crit == 0 else "CRÍTICO"],
        ["Alertas gerais",    str(n_alert), "OK" if n_alert == 0 else "ATENÇÃO"],
        ["Parecer técnico",   status, ""],
    ]

    t = _tab(dados, ws=[8*cm, 5*cm, 4*cm])
    # colore linha de parecer
    cor_parecer = COR_OK if status == "APROVADO" else COR_CRITICO
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, len(dados)-1), (-1, len(dados)-1), cor_parecer)
    ]))
    el.append(t); _sp(el)


def _dados_entrada(el, st, ent):
    _p(el, "2. DADOS DE ENTRADA", st["h2"]); _hr(el)
    campos = {
        "lamina_mm_dia":                   ("Lâmina de projeto",               "mm/dia"),
        "horas_trabalho_dia":              ("Horas de operação",                "h/dia"),
        "giro_graus":                      ("Ângulo de giro",                   "graus"),
        "area_irrigada_ha":                ("Área irrigada",                    "ha"),
        "raio_m":                          ("Raio do pivô",                     "m"),
        "pressao_pivo_mca":                ("Pressão no centro do pivô",        "mca"),
        "desnivel_captacao_para_centro":   ("Desnível captação → centro",       "m"),
        "desnivel_centro_para_ponto_alto": ("Desnível centro → ponto mais alto","m"),
        "distancia_captacao_ate_centro":   ("Distância captação → centro",      "m"),
        "k_emissor":                       ("Coef. bocal (k)",                  "m³/h"),
        "x_emissor":                       ("Expoente bocal (x)",               "—"),
    }
    dados = [["Parâmetro", "Valor", "Unidade"]]
    for ch, (nome, un) in campos.items():
        v = ent.get(ch)
        if v is not None:
            # arredonda floats com muitas casas decimais (ex: 19.9999...)
            if isinstance(v, float):
                v = round(v, 4)
            dados.append([nome, str(v), un])
    el.append(_tab(dados, ws=[8*cm, 5*cm, 4*cm])); _sp(el)


def _hidraulica(el, st, res):
    _p(el, "3. HIDRÁULICA DO PIVÔ — VÃO A VÃO", st["h2"]); _hr(el)

    r       = _resumo(res)
    trechos = res.get("pivo", {}).get("trechos", [])
    tel     = r.get("telescopia", {})

    # 3.1 resumo geral
    _p(el, "3.1 Resumo hidráulico", st["h3"])
    perda_total = r.get("P_entrada_mca", 0) - r.get("P_final_mca", 0)
    dados_r = [
        ["Parâmetro", "Valor"],
        ["Raio desejado",            f"{r.get('raio_m', 0):.1f} m"],
        ["Raio real (vãos)",         f"{r.get('raio_real_m', r.get('raio_m',0)):.2f} m"],
        ["Diferença (delta)",        f"{r.get('delta_raio_m', 0):+.2f} m"],
        ["Área irrigada",            f"{r.get('area_ha', 0):.2f} ha"],
        ["Vazão total",              f"{r.get('Q_total_m3h', 0):.2f} m³/h"],
        ["Pressão de entrada",       f"{r.get('P_entrada_mca', 0):.1f} mca"],
        ["Pressão final (L3 saída)", f"{r.get('P_final_mca', 0):.1f} mca"],
        ["Perda total no pivô",      f"{perda_total:.2f} mca"],
        ["Nº de vãos (trechos)",     str(r.get("n_trechos", 0))],
        ["Vãos com déficit pressão", str(r.get("trechos_com_deficit", 0))],
        ["CU (uniformidade)",        f"{r.get('CU_pct', 0):.1f}%"],
        ["Lâmina alvo",              f"{r.get('lamina_alvo_mm_dia', 0):.1f} mm/dia"],
        ["Lâmina média aplicada",    f"{r.get('lamina_media_mm_dia', 0):.2f} mm/dia"],
        ["Lâmina mínima",            f"{r.get('lamina_min_mm_dia', 0):.2f} mm/dia"],
        ["Lâmina máxima",            f"{r.get('lamina_max_mm_dia', 0):.2f} mm/dia"],
    ]
    # alerta de Q excessiva inline no resumo
    if r.get("Q_excede_catalogo"):
        dados_r.append(["⚠ VAZÃO EXCEDE CATÁLOGO", f"Q={r.get('Q_total_m3h',0):.0f} m³/h > {366} m³/h"])
    if r.get("reguladores_obrigatorios"):
        dados_r.append(["⚠ REGULADORES OBRIGATÓRIOS",
                        f"{r.get('n_trechos',0)} vãos — P={r.get('P_entrada_mca',0):.1f} mca > 10.5 mca"])
    el.append(_tab(dados_r, ws=[9*cm, 8*cm])); _sp(el, 6)

    # 3.2 telescopia
    _p(el, "3.2 Telescopia — diâmetros por vão", st["h3"])
    dados_t = [["Diâmetro", "Nominal", "Qtd. vãos", "Comprimento total (m)"]]
    for d_mm, info in sorted(tel.items(), key=lambda x: -int(x[0])):
        dados_t.append([
            f"{d_mm} mm",
            info.get("nome", f"{d_mm}mm"),
            str(info["vaos"]),
            f"{info['comprimento_m']:.1f} m",
        ])
    if len(dados_t) > 1:
        el.append(_tab(dados_t, ws=[4*cm, 4*cm, 4*cm, 5*cm]))
    else:
        _p(el, "Telescopia não calculada.", st["normal"])
    _sp(el, 6)

    # 3.3 tabela de vãos
    _p(el, "3.3 Tabela de vãos — Q, P e emissores", st["h3"])

    usa_cat = any(t.get("emissor",{}).get("bocal_numero") is not None
                  for t in trechos)
    cab = ["Vão", "Tipo", "r (m)", "D", "N_boc",
           "Q_in(m³/h)", "v(m/s)", "hf(mca)",
           "P_in", "P_out", "P_nec", "Déficit", "Lâmina(mm/d)"]
    if usa_cat:
        cab.insert(4, "Bocal")
    linhas = [cab]

    for t in trechos:
        e = t.get("emissor", {})
        d = e.get("deficit_pressao_mca", 0)
        # fallbacks para compatibilidade com motor antigo (sem "tipo", "diametro_nominal", etc.)
        d_nom = t.get("diametro_nominal") or f"{t.get('diametro_mm', 0)}mm"
        n_boc = str(t.get("n_bocais", "-"))
        tipo  = t.get("tipo", "-")
        bocal_str = ""
        if usa_cat:
            bn = e.get("bocal_numero")
            bc = e.get("bocal_cor","")
            bo = e.get("bocal_orificio_mm","")
            if bn: bocal_str = f"#{bn} {bc} ({bo}mm)"
        row = [
            str(t.get("indice", "-")),
            tipo,
            f"{t.get('r_ini_m',0):.0f}–{t.get('r_fim_m',0):.0f}",
            d_nom,]
        if usa_cat: row.append(bocal_str)
        row += [n_boc,
            f"{t.get('Q_in_m3h',0):.2f}",
            f"{t.get('velocidade_m_s',0):.3f}",
            f"{t.get('hf_mca',0):.3f}",
            f"{t.get('P_in_mca',0):.1f}",
            f"{t.get('P_out_mca',0):.1f}",
            f"{e.get('P_necessaria_mca',0):.1f}",
            f"{d:.1f}" if d > 0 else "—",
            f"{e.get('lamina_real_mm_dia',0):.2f}",
        ]
        linhas.append(row)

    if usa_cat:
        ws = [0.8*cm, 1.3*cm, 1.7*cm, 1.5*cm, 2.8*cm, 1.1*cm,
              1.5*cm, 1.3*cm, 1.3*cm, 1.1*cm, 1.1*cm, 1.1*cm, 1.0*cm, 1.5*cm]
    else:
        ws = [1.0*cm, 1.5*cm, 2.0*cm, 1.8*cm, 1.2*cm,
              1.8*cm, 1.5*cm, 1.5*cm, 1.3*cm, 1.3*cm, 1.3*cm, 1.3*cm, 1.8*cm]
    el.append(_tab(linhas, ws=ws)); _sp(el)

    _bocais_resumo(el, st, res)
    _reguladores_pressao(el, st, res)

    # 3.4 alertas por vão (se houver)
    alertas_vao = [(t.get("indice","-"), t.get("tipo","-"), a)
                   for t in trechos if t.get("alertas")
                   for a in (t["alertas"] if isinstance(t["alertas"], list) else [t["alertas"]])]
    if alertas_vao:
        _p(el, "3.4 Alertas por vão", st["h3"])
        for idx, tipo, a in alertas_vao:
            est = st["critico"] if "CRÍTICO" in a.upper() else st["alerta"]
            _p(el, f"Vão {idx} ({tipo}): {a}", est)
        _sp(el)



def _bocais_resumo(el, st, res):
    """Seção 3.5 — Resumo dos bocais selecionados pelo catálogo real."""
    r = _resumo(res)
    if not r.get("usa_catalogo_real"):
        return

    bocais = r.get("bocais_usados", {})
    modelo = r.get("modelo_deflector", "—")
    deflectores = {
        "cinza":  "Ângulo padrão 6 ranhuras — Gota pequena (argilas)",
        "preto":  "Ângulo padrão 9 ranhuras — Gota média (silte/franco)",
        "azul":   "Ângulo baixo 9 ranhuras — Gota média (silte/franco)",
        "branco": "Ângulo baixo 6 ranhuras — Gota grande (arenosos)",
    }
    _p(el, "3.5 Bocais selecionados — Senninger i-WOB2", st["h3"])
    _p(el, f"Fabricante: Senninger  |  Modelo: i-WOB2  |  "
           f"Deflector: {deflectores.get(modelo, modelo)}", st["mini"])
    _p(el, "Fonte: Brochure oficial Senninger — k e x calculados por regressão log-log "
           "(erro < 0,24%)", st["mini"])
    _sp(el, 4)

    if bocais:
        dados = [["Bocal", "Cor", "Orifício (mm)", "Vãos", "Total bocais", "Fabricante"]]
        for chave, info in sorted(bocais.items(),
                                   key=lambda x: float(x[1]["numero"])):
            dados.append([
                chave,
                info.get("cor", "—"),
                str(info.get("orificio_mm", "—")),
                str(info["vaos"]),
                str(info["total_bocais"]),
                "Senninger i-WOB2",
            ])
        el.append(_tab(dados, ws=[2.0*cm, 3.0*cm, 2.5*cm, 2.0*cm, 2.5*cm, 5.0*cm]))
    else:
        _p(el, "Nenhum bocal do catálogo selecionado (k/x genérico utilizado).", st["normal"])

    _sp(el, 6)


def _reguladores_pressao(el, st, res):
    """Seção 3.6 — Reguladores de pressão (obrigatórios quando P > 10.5 mca)."""
    r = _resumo(res)
    if not r.get("reguladores_obrigatorios"):
        return
    n = r.get("n_vaos_com_regulador", r.get("n_trechos", 0))
    total_reg = sum(t.get("n_bocais", 0) for t in res.get("pivo",{}).get("trechos",[]))
    _p(el, "3.6 Reguladores de pressão — ITEM OBRIGATÓRIO DE PROJETO", st["h3"])
    _p(el, (f"Pressão de entrada {r.get('P_entrada_mca',0):.1f} mca excede o máximo do bocal "
            f"Senninger i-WOB2 ({10.54:.1f} mca). Reguladores obrigatórios em todos os vãos."),
       st["critico"])
    _sp(el, 4)
    dados = [
        ["Parâmetro", "Valor"],
        ["Pressão de entrada",          f"{r.get('P_entrada_mca',0):.1f} mca"],
        ["Pressão máxima do bocal",     "10.5 mca (15 psi)"],
        ["Pressão ideal do bocal",      "7.0 mca (10 psi)"],
        ["Pressão recomendada c/ reg.", "7.0–10.5 mca"],
        ["Vãos que requerem regulador", str(r.get("n_trechos", 0))],
        ["Qtd. de reguladores",         str(total_reg)],
        ["Modelo referência",           "Senninger PSR-2 ou equivalente"],
        ["Posição de instalação",       "No topo do pendural, acima do bocal"],
    ]
    el.append(_tab(dados, ws=[9*cm, 8*cm]))
    _sp(el, 4)
    _p(el, "Atenção: sem reguladores o bocal opera acima da pressão máxima, gerando "
           "névoa excessiva, deriva pelo vento e perda de uniformidade.", st["alerta"])
    _sp(el)

def _adutora(el, st, res):
    _p(el, "4. ADUTORA", st["h2"]); _hr(el)
    adut = res.get("adutora", {})
    diam = res.get("diametro_adutora", {})
    dados = [
        ["Parâmetro", "Valor"],
        ["Diâmetro selecionado",  diam.get("nome", "—")],
        ["Diâmetro interno",      f"{diam.get('m', 0)*1000:.0f} mm"],
        ["Velocidade média",      f"{adut.get('velocidade_media_m_s', 0):.2f} m/s"],
        ["Perda de carga total",  f"{adut.get('perda_total_mca', 0):.2f} mca"],
    ]
    for i, seg in enumerate(adut.get("segmentos", []), 1):
        dados += [
            [f"Seg. {i} — comprimento",  f"{seg.get('comprimento_m',0):.0f} m"],
            [f"Seg. {i} — hf distribuída",f"{seg.get('perda_distribuida_mca',0):.3f} mca"],
            [f"Seg. {i} — hf localizada", f"{seg.get('perda_localizada_mca',0):.3f} mca"],
        ]
    el.append(_tab(dados, ws=[9*cm, 8*cm])); _sp(el)


def _bomba(el, st, res):
    _p(el, "5. BOMBA", st["h2"]); _hr(el)
    bomba = res.get("bomba_selecionada") or {}
    Q    = res.get("vazao_m3h", 0)
    hmt  = res.get("hmt_com_margem_m", 0)
    pot  = res.get("potencia_bomba_kw", 0)

    if not bomba:
        dados = [["Parâmetro", "Valor"],
                 ["Status",         "NENHUMA BOMBA DO CATÁLOGO ATENDE O PONTO"],
                 ["Q requerida",    f"{Q:.1f} m³/h"],
                 ["HMT requerida",  f"{hmt:.1f} m"],
                 ["Vazão de projeto",f"{Q:.2f} m³/h"],
                 ["HMT com margem 25%", f"{hmt:.1f} m"],
                 ["Potência instalada", f"{pot:.2f} kW"]]
        el.append(_tab(dados, ws=[9*cm, 8*cm])); _sp(el)
        return

    dados = [["Parâmetro", "Valor"],
             ["Fabricante / Linha",      f"{bomba.get('fabricante','Imbil')} — {bomba.get('linha','INI')}"],
             ["Modelo selecionado",      bomba.get("modelo", "—")],
             ["Rotação",                 f"{bomba.get('rpm','—')} rpm"],
             ["Flange sucção / recalque",f"DN{bomba.get('flange_suc_mm','—')} / DN{bomba.get('flange_rec_mm','—')} mm"],
             ["Q de projeto",            f"{Q:.1f} m³/h"],
             ["HMT de projeto (c/ 25%)", f"{hmt:.1f} m"],
             ["H @ ponto de operação",   f"{bomba.get('H_op_m', hmt):.1f} m"],
             ["Margem de HMT",           f"+{bomba.get('margem_hmt_m', 0):.1f} m"],
             ["Eficiência no ponto",     f"{bomba.get('eta_op_pct', bomba.get('eta_BEP_pct', 0)):.1f}%"],
             ["Eficiência máxima (BEP)", f"{bomba.get('eta_max_pct', 0):.1f}%"],
             ["Q no BEP",                f"{bomba.get('Q_BEP_m3h', 0):.0f} m³/h"],
             ["H no BEP",                f"{bomba.get('H_BEP_m', 0):.0f} m"],
             ["Operando perto do BEP",   "Sim ✓" if bomba.get("dentro_BEP") else "Verificar — distante do BEP"],
             ["NPSH requerido",          f"{bomba.get('NPSH_r_m', '—')} m"],
             ["Potência instalada",      f"{pot:.2f} kW ({round(pot/0.7355):.0f} CV)"],
             ["Fonte",                   "Catálogo Imbil INI — Ed. 12/2015 (curvas reais)"],
            ]
    el.append(_tab(dados, ws=[9*cm, 8*cm]))
    _sp(el, 4)
    if not bomba.get("dentro_BEP"):
        _p(el, "⚠ Bomba operando distante do BEP — verificar com fabricante se ponto é "
               "aceitável para operação contínua.", st["alerta"])
    _sp(el)


def _energia(el, st, res, ent):
    _p(el, "6. ANÁLISE ENERGÉTICA", st["h2"]); _hr(el)
    pot   = res.get("potencia_bomba_kw", 0)
    horas = ent.get("horas") or ent.get("horas_trabalho_dia") or 20
    area  = res.get("area_ha", 1) or 1
    tar   = 0.85
    dados = [
        ["Parâmetro", "Valor"],
        ["Consumo diário",              f"{pot*horas:.1f} kWh"],
        ["Consumo mensal",              f"{pot*horas*30:.1f} kWh"],
        ["Custo mensal (R$ 0,85/kWh)", f"R$ {pot*horas*30*tar:.2f}"],
        ["Custo anual",                 f"R$ {pot*horas*30*12*tar:.2f}"],
        ["Custo por hectare",           f"R$ {(pot*horas*30*tar)/area:.2f}/ha/mês"],
    ]
    el.append(_tab(dados, ws=[9*cm, 8*cm])); _sp(el)


def _alertas_pdf(el, st, alertas):
    _p(el, "7. ALERTAS E VALIDAÇÕES", st["h2"]); _hr(el)
    if not alertas:
        _p(el, "✅ Nenhum alerta — projeto dentro dos parâmetros técnicos.", st["ok"])
    else:
        n_crit = sum(1 for a in alertas if "CRÍTICO" in a.upper())
        _p(el, f"Total: {len(alertas)} alerta(s) | Críticos: {n_crit}", st["mini"])
        _sp(el, 4)
        for a in alertas:
            upper = a.upper()
            if "CRÍTICO" in upper:
                est, pre = st["critico"], "🔴 [CRÍTICO]"
            elif "ALERTA" in upper:
                est, pre = st["alerta"], "🟡 [ALERTA]"
            else:
                est, pre = st["normal"], "ℹ️ [INFO]"
            _p(el, f"{pre} {a}", est)
            _sp(el, 2)
    _sp(el)


def _sugestoes_pdf(el, st, sugestoes):
    _p(el, "8. SUGESTÕES E CENÁRIOS DE OTIMIZAÇÃO", st["h2"]); _hr(el)
    if not sugestoes:
        _p(el, "Sem sugestões adicionais.", st["normal"]); return
    for i, sug in enumerate(sugestoes, 1):
        tipo    = sug.get("tipo","").replace("_"," ").upper()
        msg     = sug.get("mensagem","")
        acoes   = sug.get("acoes", [])
        impacto = sug.get("impacto_estimado","")
        params  = sug.get("parametros", {})
        _p(el, f"{i}. [{tipo}] {msg}", st["h3"])
        for k, v in params.items():
            _p(el, f"   • {k.replace('_',' ')}: {v}", st["mini"])
        for acao in acoes:
            _p(el, f"   → {acao}", st["normal"])
        if impacto:
            _p(el, f"   Impacto estimado: {impacto}", st["mini"])
        _sp(el, 4)
    _sp(el)



def _bom_pdf(el, st, bom: dict):
    """Seção 9 — Lista de Materiais (BOM) por seção."""
    _p(el, "9. LISTA DE MATERIAIS (BOM)", st["h2"]); _hr(el)

    if not bom or not bom.get("secoes"):
        _p(el, "BOM não disponível — verifique se lista_materiais_service está instalado.",
           st["normal"]); return

    resumo_bom = bom.get("resumo", {})
    dados_res = [
        ["Parâmetro", "Valor"],
        ["Total de seções",   str(resumo_bom.get("n_secoes", 0))],
        ["Total de itens",    str(resumo_bom.get("n_itens_total", 0))],
        ["Raio real",         f"{resumo_bom.get('raio_real_m', 0):.2f} m"],
        ["Área irrigada",     f"{resumo_bom.get('area_ha', 0):.2f} ha"],
        ["Vazão total",       f"{resumo_bom.get('Q_m3h', 0):.1f} m³/h"],
        ["HMT (c/ margem)",   f"{resumo_bom.get('hmt_m', 0):.1f} m"],
        ["Potência motor",    f"{resumo_bom.get('potencia_kw', 0):.1f} kW "
                              f"({resumo_bom.get('potencia_cv', 0):.0f} CV)"],
    ]
    el.append(_tab(dados_res, ws=[9*cm, 8*cm])); _sp(el, 8)

    COR_BOM_H = colors.HexColor("#0f3460")
    COR_LINHA_A = colors.HexColor("#f5f8fa")

    for sec in bom["secoes"]:
        t_sec = Table(
            [[f"{sec['codigo']} — {sec['titulo']}", sec.get("subtitulo", "")]],
            colWidths=[10*cm, 7*cm]
        )
        t_sec.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), COR_BOM_H),
            ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,0), 9),
            ("TOPPADDING",    (0,0), (-1,0), 5),
            ("BOTTOMPADDING", (0,0), (-1,0), 5),
        ]))
        el.append(t_sec); _sp(el, 2)

        cab = ["Item", "Descrição", "Especificação", "Un.", "Qtd.", "Obs."]
        linhas = [cab]
        for it in sec["itens"]:
            linhas.append([
                str(it["seq"]),
                it["descricao"],
                it["especificacao"],
                it["unidade"],
                str(it["quantidade"]),
                it.get("observacao", ""),
            ])
        ws_bom = [1.0*cm, 4.5*cm, 5.0*cm, 1.0*cm, 1.0*cm, 4.5*cm]
        t_it = Table(linhas, colWidths=ws_bom, repeatRows=1)
        t_it.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), colors.HexColor("#2f6690")),
            ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 7.5),
            ("ALIGN",         (0,0), (-1,-1), "LEFT"),
            ("ALIGN",         (4,0), (4,-1), "CENTER"),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, COR_LINHA_A]),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]))
        el.append(t_it); _sp(el, 10)
    _sp(el)


def _agronomia(el, st, res):
    """Seção 10 — Análise Agronômica (quando disponível)."""
    agro = res.get("agronomia")
    if not agro:
        return
    _p(el, "10. ANÁLISE AGRONÔMICA", st["h2"]); _hr(el)

    lam  = agro.get("lamina", {})
    tv   = agro.get("taxa_aplicacao", {})
    dem  = agro.get("demanda_total", {})

    dados = [["Parâmetro", "Valor"],
             ["Cultura",                lam.get("cultura","—")],
             ["Região climática",       lam.get("regiao","—")],
             ["Tipo de solo",           lam.get("solo","—")],
             ["Fase fenológica",        lam.get("fase","—").upper()],
             ["ETo (ref.)",             f"{lam.get('ETo_mm_d',0):.2f} mm/dia"],
             ["Kc (coef. de cultura)",  f"{lam.get('Kc',0):.3f}"],
             ["ETc (evapotransp. cultura)", f"{lam.get('ETc_mm_d',0):.2f} mm/dia"],
             ["CAD disponível no perfil",   f"{lam.get('CAD_total_mm',0):.1f} mm"],
             ["Fração de depleção (p)",     f"{lam.get('f_dep',0):.2f}"],
             ["Lâmina líquida por evento",  f"{lam.get('lamina_liq_mm',0):.1f} mm"],
             ["Eficiência de aplicação",    f"{lam.get('eficiencia_aplic',0)*100:.0f}%"],
             ["Lâmina bruta por evento",    f"{lam.get('lamina_bruta_mm',0):.1f} mm"],
             ["Turno de rega",              f"{lam.get('turno_rega_d',0)} dias"],
             ["Lâmina diária equivalente",  f"{lam.get('lamina_dia_mm',0):.2f} mm/dia"],
             ["Ciclo da cultura",           f"{lam.get('ciclo_dias',0)} dias"],
             ["Prof. radicular",            f"{lam.get('z_rad_m',0):.2f} m"],
            ]
    el.append(_tab(dados, ws=[9*cm, 8*cm])); _sp(el, 6)

    # Taxa de aplicação
    if tv:
        cor_tv = st["critico"] if tv.get("risco_runoff") else st["ok"]
        _p(el, f"Taxa de Aplicação (TAL): {tv.get('TAL_mm_h',0):.2f} mm/h  |  "
               f"TIB do solo: {tv.get('TIB_mm_h',0)} mm/h  |  {tv.get('status','')}", cor_tv)
        if tv.get("risco_runoff"):
            _p(el, f"⚠ {tv.get('recomendacao','')}", st["alerta"])
        _sp(el, 4)

    # Demanda total
    if dem:
        _p(el, f"Demanda hídrica total do ciclo ({dem.get('ciclo_dias',0)} dias): "
               f"ETc média {dem.get('ETc_medio_mm_d',0):.2f} mm/dia  |  "
               f"Volume bruto estimado: {dem.get('vol_bruto_m3',0):,.0f} m³  "
               f"({dem.get('area_ha',0):.2f} ha)", st["normal"])
    _sp(el, 4)
    _p(el, "Fontes: FAO-56 (Allen et al., 1998) / Embrapa Milho e Sorgo / INMET.", st["normal"])
    _sp(el)

def _conclusao(el, st, alertas, res):
    _p(el, "9. CONCLUSÃO TÉCNICA", st["h2"]); _hr(el)
    r      = _resumo(res)
    n_crit = sum(1 for a in alertas if "CRÍTICO" in a.upper())
    P_ok   = r.get("pressao_final_ok", False)
    cu     = r.get("CU_pct", 0)

    criticos_h = [a for a in alertas
                  if "CRÍTICO" in a.upper()
                  and "REGULADOR" not in a.upper()
                  and "PSR" not in a.upper()]
    so_reg = (n_crit > 0 and len(criticos_h) == 0)
    if criticos_h or (n_crit > 0 and not so_reg) or not P_ok:
        parecer = ("O projeto apresenta RESTRIÇÕES CRÍTICAS que impedem a execução "
                   "conforme dimensionado. Correções obrigatórias antes da implantação.")
        est = st["critico"]
    elif so_reg:
        parecer = ("Projeto APROVADO COM RESSALVAS. Hidráulica adequada. "
                   "Instalar reguladores PSR-2 em todos os vãos antes da operação.")
        est = st["alerta"]
    elif cu < 80 or len(alertas) > 3:
        parecer = ("O projeto é TECNICAMENTE VIÁVEL com as ressalvas indicadas. "
                   "Recomenda-se implementar as sugestões antes da implantação.")
        est = st["alerta"]
    else:
        parecer = ("Projeto APROVADO tecnicamente. Todos os parâmetros hidráulicos "
                   "estão dentro dos limites aceitáveis.")
        est = st["ok"]

    _p(el, parecer, est); _sp(el, 6)
    _p(el, (f"Raio real: {r.get('raio_real_m', r.get('raio_m',0)):.1f} m  |  "
            f"Pressão final: {r.get('P_final_mca',0):.1f} mca  |  "
            f"CU: {cu:.1f}%  |  "
            f"Alertas: {len(alertas)}  |  Críticos: {n_crit}"), st["mini"])
    _sp(el, 6)
    _p(el, "Relatório gerado automaticamente — validar em campo após implantação.",
       st["mini"])


# ─────────────────────────────────────────────────────────────
# PÚBLICA
# ─────────────────────────────────────────────────────────────

def gerar_relatorio_pdf(data: dict) -> str:
    resultado = data.get("resultado") or {}
    entrada   = (data.get("dados_entrada")
                 or resultado.get("entrada")
                 or {})

    caminho = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(
        caminho, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
    )
    st = _st(); el = []

    _capa(el, st, resultado, entrada)
    _resumo_exec(el, st, resultado)
    el.append(PageBreak())

    _dados_entrada(el, st, entrada)
    _hidraulica(el, st, resultado)
    el.append(PageBreak())

    _adutora(el, st, resultado)
    _bomba(el, st, resultado)
    _energia(el, st, resultado, entrada)
    el.append(PageBreak())

    _alertas_pdf(el, st, resultado.get("alertas", []))
    el.append(PageBreak())

    _sugestoes_pdf(el, st, resultado.get("sugestoes", []))
    el.append(PageBreak())

    _bom_pdf(el, st, resultado.get("bom", {}))
    el.append(PageBreak())

    _agronomia(el, st, resultado)
    _conclusao(el, st, resultado.get("alertas", []), resultado)

    doc.build(el)
    return caminho
