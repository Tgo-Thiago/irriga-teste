"""
dimensionamento_service.py
Orquestra toda a cadeia de cálculo do pivô central.
Versão unificada: bocais reais + velocidade angular + BOM integrado.
"""

import math
from core.motor_pivo import calcular_pivo
from core.adutora import calcular_adutora, escolher_diametro_adutora
from core.bomba import calcular_hmt, calcular_potencia
from core.catalogo_bombas import selecionar_bomba
from services.validacao import validar_projeto
from services.sugestoes import gerar_sugestoes
from services.lista_materiais_service import gerar_bom


def _raio_ideal(area_ha, giro_graus):
    return math.sqrt(area_ha * 10000 / (math.pi * (giro_graus / 360)))

def _area_ha(raio_m, giro_graus):
    return math.pi * raio_m**2 * (giro_graus / 360) / 10000

def _normalizar(req: dict) -> dict:
    d = req.copy()
    d["horas"] = d.get("horas_trabalho_dia") or d.get("horas_trabalho")
    if not d["horas"]:
        raise ValueError("Horas de operação não informadas")
    d["desnivel_succao"]         = d.get("desnivel_captacao_para_centro", 0)
    d["desnivel_recalque"]       = d.get("desnivel_centro_para_ponto_alto", 0)
    d["eficiencia"]              = d.get("eficiencia", 0.72)
    d["pressao_pivo"]            = d.get("pressao_pivo_mca", 25)
    d["k_emissor"]               = d.get("k_emissor", 0.7)
    d["x_emissor"]               = d.get("x_emissor", 0.5)
    d["espacamento_emissores_m"] = d.get("espacamento_emissores_m", 5.0)
    # modelo do deflector (catálogo real)
    raw = d.get("modelo_deflector", "preto")
    d["modelo_deflector"] = raw if raw in ("cinza","preto","azul","branco") else "preto"
    # velocidade angular
    d["velocidade_percentual"]      = float(d.get("velocidade_percentual", 0) or 0)
    d["v_max_ultima_torre_m_min"]   = float(d.get("v_max_ultima_torre_m_min", 2.2) or 2.2)
    return d


def _dimensionar_base(dados: dict) -> dict:

    # 1. GEOMETRIA
    if dados.get("raio_m"):
        raio = dados["raio_m"]
        area = _area_ha(raio, dados["giro_graus"])
    else:
        raio = _raio_ideal(dados["area_irrigada_ha"], dados["giro_graus"])
        area = dados["area_irrigada_ha"] * (dados["giro_graus"] / 360)
    dados["raio_m"] = round(raio, 2)

    # 2. MOTOR HIDRÁULICO
    resultado_pivo = calcular_pivo(
        raio_m                   = raio,
        lamina_mm_dia            = dados["lamina_mm_dia"],
        horas_dia                = dados["horas"],
        P_entrada_mca            = dados["pressao_pivo"],
        k_emissor_m3h            = dados["k_emissor"],
        x_emissor                = dados["x_emissor"],
        espacamento_m            = dados["espacamento_emissores_m"],
        perfil_terreno           = dados.get("perfil_terreno"),
        modelo_deflector         = dados["modelo_deflector"],
        velocidade_percentual    = dados["velocidade_percentual"],
        v_max_ultima_torre_m_min = dados["v_max_ultima_torre_m_min"],
    )

    if "erro" in resultado_pivo:
        resultado_pivo = {
            "trechos": [],
            "resumo":  {"Q_total_m3h": 0, "P_final_mca": 0, "CU_pct": 0},
            "alertas": [f"Falha no motor: {resultado_pivo['erro']}"],
        }

    Q_total_m3h = resultado_pivo["resumo"]["Q_total_m3h"]

    # 3. ADUTORA
    diam_adutora      = escolher_diametro_adutora(Q_total_m3h)
    segmentos_adutora = [{
        "diametro_interno_m": diam_adutora["m"],
        "comprimento_m":      dados.get("distancia_captacao_ate_centro", 100),
        "componentes": [
            {"tipo": "entrada",               "quantidade": 1},
            {"tipo": "curva_90",              "quantidade": 2},
            {"tipo": "valvula_gaveta_aberta", "quantidade": 1},
            {"tipo": "valvula_retencao",      "quantidade": 1},
            {"tipo": "filtro",                "quantidade": 1},
            {"tipo": "saida",                 "quantidade": 1},
        ]
    }]
    adutora = calcular_adutora(Q_total_m3h, segmentos_adutora)

    # 4. HMT + BOMBA
    hmt        = calcular_hmt(dados["desnivel_succao"], dados["desnivel_recalque"],
                               adutora["perda_total_mca"], pressao_pivo=dados["pressao_pivo"])
    hmt_real   = hmt * 1.25
    bomba      = selecionar_bomba(Q_total_m3h, hmt_real, margem_hmt=1.0)
    eficiencia = bomba["eficiencia"] if bomba else dados["eficiencia"]
    potencia   = calcular_potencia(Q_total_m3h, hmt_real, eficiencia)

    res = {
        "entrada":           dados,
        "area_ha":           round(area, 2),
        "vazao_m3h":         round(Q_total_m3h, 3),
        "pivo":              resultado_pivo,
        "adutora":           adutora,
        "diametro_adutora":  diam_adutora,
        "hmt_m":             round(hmt, 2),
        "hmt_com_margem_m":  round(hmt_real, 2),
        "bomba_selecionada": bomba,
        "potencia_bomba_kw": potencia,
        "pressao_pivo_real": round(dados["pressao_pivo"], 2),
    }
    return res


def dimensionar(request: dict) -> dict:
    try:
        dados = _normalizar(request)
        res   = _dimensionar_base(dados)
        res["alertas"]   = validar_projeto(res)
        res["sugestoes"] = gerar_sugestoes(res)

        # BOM integrado
        config_bom = {
            "modelo_emissor":       request.get("modelo_emissor", "Senninger i-WOB2"),
            "motoredutor":          request.get("motoredutor", "Alta velocidade — padrão"),
            "pneu":                 request.get("pneu", '12.4" aro 24"'),
            "painel":               request.get("painel_controle", "Completo mecânico"),
            "n_hastes_aterramento": request.get("n_hastes_aterramento", 4),
            "parada_setorial":      request.get("parada_setorial", False),
        }
        try:
            res["bom"] = gerar_bom(res, config_bom)
        except Exception as e:
            res["bom"] = {"erro": str(e), "secoes": [], "resumo": {}}

        return res
    except Exception as e:
        raise Exception(f"Erro no dimensionamento: {e}")
