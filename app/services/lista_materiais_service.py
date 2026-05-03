"""
lista_materiais_service.py
==========================
Gera o BOM (Bill of Materials) completo do pivô central.

Baseado na proposta comercial Romera Simon como referência de estrutura.
Cada módulo é independente e recebe os dados já calculados pelo motor.

Estrutura do BOM:
  01 — Pivô central (estrutura, vãos, torres, emissores, painel)
  02 — Conjunto de bombeamento
  03 — Adutora / conexões
  04 — Conjunto elétrico

Cada item tem: { seq, descricao, especificacao, unidade, quantidade, observacao }
"""

import math


# ── constantes de catálogo ───────────────────────────────────

COMPRIM_TUBO_ADUTORA_M = 6.0   # comprimento padrão do tubo PVC
ESPAC_BOCAIS_M         = 2.5   # espaçamento entre bocais (definido no motor)
COMPRIM_CABO_EXTRA_M   = 50    # margem de cabos além da distância de captação

# Tabela CV → polos/RPM/soft-start para motor elétrico
TABELA_MOTOR = [
    {"cv_min":  1, "cv_max":   7.5, "polos": 4, "rpm_nom": 1750, "corr_a": 16,  "softstart": "ASW-01 16A"},
    {"cv_min":  7.5,"cv_max": 15,   "polos": 4, "rpm_nom": 1750, "corr_a": 30,  "softstart": "ASW-02 30A"},
    {"cv_min": 15, "cv_max":  25,   "polos": 2, "rpm_nom": 3500, "corr_a": 45,  "softstart": "ASW-04 45A"},
    {"cv_min": 25, "cv_max":  40,   "polos": 2, "rpm_nom": 3500, "corr_a": 75,  "softstart": "ASW-05 75A"},
    {"cv_min": 40, "cv_max":  75,   "polos": 2, "rpm_nom": 3500, "corr_a": 125, "softstart": "ASW-06 125A"},
    {"cv_min": 75, "cv_max": 150,   "polos": 2, "rpm_nom": 3500, "corr_a": 200, "softstart": "ASW-07 200A"},
]

# Bomba: diâm. sucção / recalque por faixa de vazão
TABELA_BOMBA_CONEXOES = [
    {"q_min":  0, "q_max":  30,  "suc": '2 1/2"', "rec": '3"'},
    {"q_min": 30, "q_max":  80,  "suc": '3"',     "rec": '4"'},
    {"q_min": 80, "q_max": 200,  "suc": '4"',     "rec": '4"'},
    {"q_min":200, "q_max": 500,  "suc": '6"',     "rec": '6"'},
]

# Autotrafo: KVA por faixa de CV do motor
TABELA_AUTOTRAFO = [
    {"cv_min":  1, "cv_max": 10,  "kva":  10},
    {"cv_min": 10, "cv_max": 20,  "kva":  15},
    {"cv_min": 20, "cv_max": 30,  "kva":  20},
    {"cv_min": 30, "cv_max": 50,  "kva":  30},
    {"cv_min": 50, "cv_max": 75,  "kva":  50},
    {"cv_min": 75, "cv_max":150,  "kva":  75},
]


# ── helpers internos ─────────────────────────────────────────

def _item(seq, descricao, especificacao, unidade, quantidade, observacao=""):
    return {
        "seq":          seq,
        "descricao":    descricao,
        "especificacao":especificacao,
        "unidade":      unidade,
        "quantidade":   quantidade,
        "observacao":   observacao,
    }

def _kw_para_cv(kw):
    return round(kw / 0.7355, 1)

def _lookup(tabela, valor, campo_min="cv_min", campo_max="cv_max"):
    for row in tabela:
        if row[campo_min] <= valor <= row[campo_max]:
            return row
    return tabela[-1]  # fallback: maior faixa


# ── MÓDULO 01: PIVÔ CENTRAL ──────────────────────────────────

def _bom_pivo(trechos: list, raio_real_m: float, config: dict) -> list:
    """
    Gera itens de BOM da estrutura do pivô.
    config: opções do usuário (modelo_emissor, modelo_pneu, etc.)
    """
    itens = []
    seq   = 1

    # Agrupa vãos por diâmetro e tipo
    tipos = {}
    for t in trechos:
        key = (t.get("diametro_nominal", "?"), t.get("tipo", "?"))
        tipos.setdefault(key, {"qtd": 0, "comp_total": 0.0})
        tipos[key]["qtd"]        += 1
        tipos[key]["comp_total"] += t.get("comprimento_m", 0)

    # Vãos galvanizados
    for (diam_nom, tipo), info in sorted(tipos.items(), key=lambda x: -x[1]["comp_total"]):
        descricao = f"Vão {tipo.upper()} — tubo galvanizado"
        espec     = (f"{diam_nom} × {info['comp_total']/info['qtd']:.2f} m | "
                     f"esp. {config.get('espessura_mm', 2.65)} mm")
        itens.append(_item(seq, descricao, espec, "un", info["qtd"],
                           f"Comprimento total: {info['comp_total']:.2f} m"))
        seq += 1

    # Torres (1 por vão, exceto L3)
    vaos_principais = [t for t in trechos if not t.get("balanco", False)]
    n_torres = len(vaos_principais)
    itens.append(_item(seq, "Torres de sustentação", "Aço galvanizado", "un", n_torres,
                       "1 torre por vão principal"))
    seq += 1

    # Motoredutores
    itens.append(_item(seq, "Motoredutor de alta velocidade",
                       config.get("motoredutor", "Marca padrão — Alta velocidade"),
                       "un", n_torres, "1 por torre"))
    seq += 1

    # Redutores de roda
    itens.append(_item(seq, "Redutor de roda",
                       config.get("redutor_roda", "Cestari 1:50"),
                       "un", n_torres * 2, "2 por torre (1 por roda)"))
    seq += 1

    # Pneus
    itens.append(_item(seq, "Pneu de irrigação",
                       config.get("pneu", '12.4" aro 24"'),
                       "un", n_torres * 2, "2 por torre"))
    seq += 1

    # Emissores (bocais) — soma de n_bocais por vão
    total_bocais = sum(t.get("n_bocais", 0) for t in trechos)
    modelo_em    = config.get("modelo_emissor", "Senninger I-Wobler")
    itens.append(_item(seq, f"Emissor / bocal — {modelo_em}",
                       f"Modelo {modelo_em} | espaç. {ESPAC_BOCAIS_M} m",
                       "un", total_bocais,
                       f"Distribuídos em {len(trechos)} vãos"))
    seq += 1

    # Pendurais (1 por emissor)
    itens.append(_item(seq, "Pendural — mangueira flexível",
                       "Mang. flex. com conector",
                       "un", total_bocais, "1 por emissor"))
    seq += 1

    # Painel de controle
    itens.append(_item(seq, "Painel de controle",
                       config.get("painel", "Completo mecânico"),
                       "un", 1))
    seq += 1

    # Curva dupla na base
    itens.append(_item(seq, "Curva dupla na base",
                       config.get("curva_base", '8" DIN'),
                       "un", 1))
    seq += 1

    # Anel coletor
    itens.append(_item(seq, "Anel coletor",
                       config.get("anel_coletor", "11 pistas"),
                       "un", 1))
    seq += 1

    # Aterramento
    n_hastes = config.get("n_hastes_aterramento", 4)
    itens.append(_item(seq, "Haste de aterramento",
                       "Cobre — 5/8\" × 2,4 m",
                       "un", n_hastes))
    seq += 1

    # Acessórios adicionais
    if config.get("parada_setorial", False):
        itens.append(_item(seq, "Parada setorial",
                           "Parada automática setorial",
                           "un", 1))
        seq += 1

    return itens


# ── MÓDULO 02: BOMBEAMENTO ───────────────────────────────────

def _bom_bombeamento(res: dict) -> list:
    itens  = []
    seq    = 1
    pot_kw = res.get("potencia_bomba_kw", 0) or 0
    Q_m3h  = res.get("vazao_m3h", 0) or 0
    hmt    = res.get("hmt_com_margem_m", 0) or 0
    bomba  = res.get("bomba_selecionada") or {}

    cv = _kw_para_cv(pot_kw)
    motor_info = _lookup(TABELA_MOTOR, cv)
    conn_info  = _lookup(TABELA_BOMBA_CONEXOES, Q_m3h, "q_min", "q_max")

    # Motor elétrico
    itens.append(_item(seq, "Motor elétrico trifásico",
                       f"II Polos {motor_info['rpm_nom']} RPM {cv:.0f} CV (4T)",
                       "un", 1,
                       f"Potência calculada: {pot_kw:.2f} kW"))
    seq += 1

    # Bomba centrífuga
    modelo_bomba = bomba.get("modelo", f"Bomba Q={Q_m3h:.0f}m³/h HMT={hmt:.0f}m")
    itens.append(_item(seq, "Bomba centrífuga monoestágio",
                       f"{modelo_bomba} | Q={Q_m3h:.1f} m³/h | HMT={hmt:.1f} m",
                       "un", 1))
    seq += 1

    # Base fixa
    itens.append(_item(seq, "Base fixa com acoplamento",
                       f"Para motobomba {cv:.0f} CV",
                       "un", 1))
    seq += 1

    # Conjunto de sucção
    itens.append(_item(seq, "Conjunto de sucção A.Z.",
                       f"{conn_info['suc']} RS × 2½\" DIN c/ válvula de pé",
                       "un", 1))
    seq += 1

    # Conjunto de saída/recalque
    itens.append(_item(seq, "Conjunto de saída A.Z.",
                       f"c/ retenção {conn_info['rec']} RS × {conn_info['rec']} DIN / Reg. Gav.",
                       "un", 1))
    seq += 1

    # Soft-start
    itens.append(_item(seq, "Chave partida Soft-Start",
                       f"{motor_info['softstart']} 220–440 V {cv:.0f} CV",
                       "un", 1))
    seq += 1

    return itens


# ── MÓDULO 03: ADUTORA ───────────────────────────────────────

def _bom_adutora(res: dict) -> list:
    itens   = []
    seq     = 1
    adutora = res.get("adutora", {})
    diam    = res.get("diametro_adutora", {})
    entrada = res.get("entrada", {})

    comprimento_m = entrada.get("distancia_captacao_ate_centro", 100) or 100
    D_mm  = round((diam.get("m", 0.15)) * 1000)
    D_nom = diam.get("nome", f"{D_mm} mm")

    # material padrão: PVC PN60 (pressão nominal compatível com irrigação)
    # determina PN pelo diâmetro
    pn = 80 if D_mm <= 100 else 60

    # número de tubos necessários (arredonda para cima + 5% de sobra)
    n_tubos = math.ceil(comprimento_m / COMPRIM_TUBO_ADUTORA_M * 1.05)

    itens.append(_item(seq, "Tubo PVC adutora",
                       f"{D_mm} mm PN{pn} × {COMPRIM_TUBO_ADUTORA_M:.1f} m",
                       "un", n_tubos,
                       f"Comprimento adutora: {comprimento_m:.0f} m + 5% sobra"))
    seq += 1

    # extremidades flange
    itens.append(_item(seq, "Extremidade bolsa × flange DIN",
                       f"{D_mm} mm",
                       "un", 2,
                       "1 no início (captação) + 1 no final (centro pivô)"))
    seq += 1

    # joelhos / curvas (mínimo 2 — uma na captação, uma no centro)
    itens.append(_item(seq, "Joelho 90° PVC",
                       f"{D_mm} mm PN{pn}",
                       "un", 2,
                       "Quantidade mínima — ajustar conforme traçado"))
    seq += 1

    # válvula de gaveta
    itens.append(_item(seq, "Válvula de gaveta",
                       f"{D_mm} mm (4\" DIN)",
                       "un", 1,
                       "Registro de bloqueio na saída da bomba"))
    seq += 1

    # filtro de tela
    itens.append(_item(seq, "Filtro de tela / areia",
                       f"Entrada {D_mm} mm",
                       "un", 1,
                       "Proteção do sistema de irrigação"))
    seq += 1

    return itens


# ── MÓDULO 04: ELÉTRICO ──────────────────────────────────────

def _bom_eletrico(res: dict) -> list:
    itens   = []
    seq     = 1
    pot_kw  = res.get("potencia_bomba_kw", 0) or 0
    entrada = res.get("entrada", {})

    cv   = _kw_para_cv(pot_kw)
    dist = (entrada.get("distancia_captacao_ate_centro", 100) or 100) + COMPRIM_CABO_EXTRA_M
    comp = math.ceil(dist)

    motor_info   = _lookup(TABELA_MOTOR, cv)
    autotr_info  = _lookup(TABELA_AUTOTRAFO, cv)

    # Cabo de aterramento (cobre nu)
    itens.append(_item(seq, "Cabo de cobre nu",
                       "16 mm²",
                       "m", comp,
                       "Aterramento — do padrão elétrico até a motobomba"))
    seq += 1

    # Cabo de comando / sinalização
    itens.append(_item(seq, "Cabo de cobre — comando",
                       "2 × 2,5 mm² 1kV",
                       "m", comp,
                       "Sinalização painel pivô ↔ casa de bombas"))
    seq += 1

    # Cabo de força trifásico
    secao = 16 if cv <= 25 else (25 if cv <= 40 else 35)
    itens.append(_item(seq, "Cabo de cobre — força trifásico",
                       f"3 × {secao} mm² 1kV",
                       "m", comp,
                       "Alimentação motobomba"))
    seq += 1

    # CJ cabos ligação motobomba / soft-start
    itens.append(_item(seq, "CJ cabos ligação motobomba — Soft-Start",
                       f"{cv:.0f} CV | {motor_info['softstart']} 380 V",
                       "cj", 1))
    seq += 1

    # CJ cabos ligação autotrafo
    itens.append(_item(seq, "CJ cabos ligação autotrafo externo",
                       "Casa de bombas",
                       "cj", 1))
    seq += 1

    # Autotrafo
    itens.append(_item(seq, "Autotrafo trifásico a óleo",
                       f"{autotr_info['kva']} KVA 220-380 / 500 V",
                       "un", 1,
                       f"Para motor de {cv:.0f} CV"))
    seq += 1

    return itens


# ── FUNÇÃO PRINCIPAL ─────────────────────────────────────────

def gerar_bom(res: dict, config_usuario: dict = None) -> dict:
    """
    Gera o BOM completo a partir do resultado do dimensionamento.

    Parâmetros
    ----------
    res            : resultado completo do dimensionamento_service
    config_usuario : opções opcionais do usuário (modelo_emissor, pneu, etc.)

    Retorna
    -------
    {
      secoes: [
        { codigo, titulo, itens: [...] }
      ],
      resumo: { n_itens_total, ... }
    }
    """
    cfg = config_usuario or {}
    cfg.setdefault("espessura_mm",          2.65)
    cfg.setdefault("modelo_emissor",        "Senninger I-Wobler")
    cfg.setdefault("motoredutor",           "Alta velocidade — padrão")
    cfg.setdefault("redutor_roda",          "Cestari 1:50")
    cfg.setdefault("pneu",                  '12.4" aro 24"')
    cfg.setdefault("painel",                "Completo mecânico")
    cfg.setdefault("curva_base",            '8" DIN')
    cfg.setdefault("anel_coletor",          "11 pistas")
    cfg.setdefault("n_hastes_aterramento",  4)
    cfg.setdefault("parada_setorial",       False)

    pivo    = res.get("pivo", {})
    resumo  = pivo.get("resumo", {})
    trechos = pivo.get("trechos", [])

    itens_01 = _bom_pivo(trechos, resumo.get("raio_real_m", 0), cfg)
    itens_02 = _bom_bombeamento(res)
    itens_03 = _bom_adutora(res)
    itens_04 = _bom_eletrico(res)

    secoes = [
        {"codigo": "01", "titulo": "PIVÔ CENTRAL",
         "subtitulo": f"Fixo | {resumo.get('raio_real_m', 0):.2f} m | "
                      f"{resumo.get('area_ha', 0):.2f} ha | 360°",
         "itens": itens_01},
        {"codigo": "02", "titulo": "CONJUNTO DE BOMBEAMENTO",
         "subtitulo": f"Q={res.get('vazao_m3h',0):.1f} m³/h | HMT={res.get('hmt_com_margem_m',0):.1f} m | "
                      f"P={res.get('potencia_bomba_kw',0):.1f} kW",
         "itens": itens_02},
        {"codigo": "03", "titulo": "ADUTORA / CONEXÕES",
         "subtitulo": f"D={res.get('diametro_adutora',{}).get('nome','—')} | "
                      f"L={res.get('entrada',{}).get('distancia_captacao_ate_centro',100):.0f} m",
         "itens": itens_03},
        {"codigo": "04", "titulo": "CONJUNTO ELÉTRICO",
         "subtitulo": f"Cabos + soft-start + autotrafo | "
                      f"{_kw_para_cv(res.get('potencia_bomba_kw',0)):.0f} CV",
         "itens": itens_04},
    ]

    total_itens = sum(len(s["itens"]) for s in secoes)

    return {
        "secoes":  secoes,
        "resumo": {
            "n_secoes":      len(secoes),
            "n_itens_total": total_itens,
            "raio_real_m":   resumo.get("raio_real_m", 0),
            "area_ha":       resumo.get("area_ha", 0),
            "Q_m3h":         res.get("vazao_m3h", 0),
            "hmt_m":         res.get("hmt_com_margem_m", 0),
            "potencia_kw":   res.get("potencia_bomba_kw", 0),
            "potencia_cv":   _kw_para_cv(res.get("potencia_bomba_kw", 0)),
        },
    }
