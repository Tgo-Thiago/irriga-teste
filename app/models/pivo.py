from typing import List, Optional
from pydantic import BaseModel

class Vao(BaseModel):
    tipo: str
    quantidade: int

class DadosEntrada(BaseModel):
    lamina_mm_dia: float
    horas_trabalho_dia: float
    area_irrigada_ha: float
    giro_graus: float

    # -------------------------
    # DESNÍVEIS
    # -------------------------
    desnivel_captacao_para_centro: float = 0
    desnivel_centro_para_ponto_alto: float = 0
    desnivel_centro_para_ponto_baixo: float = 0

    # -------------------------
    # DISTÂNCIA
    # -------------------------
    distancia_captacao_ate_centro: float = 0

    # -------------------------
    # PRESSÃO
    # -------------------------
    pressao_pivo_mca: float = 25

    # -------------------------
    # RAIO (IMPORTANTE PRO FRONT)
    # -------------------------
    raio_m: Optional[float] = None

    # -------------------------
    # VÃOS (AGORA OPCIONAL)
    # -------------------------
    vaos: Optional[List[Vao]] = None

class ProjetoPivo(BaseModel):
    user_id: Optional[str] = None
    user_type: str
    dados_entrada: DadosEntrada
    status: Optional[str] = "em_andamento"
