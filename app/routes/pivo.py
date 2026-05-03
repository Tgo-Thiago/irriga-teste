import asyncio
import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Dict

from dependencies.auth import get_current_user
from services.dimensionamento_service import dimensionar
from services.relatorio_service import gerar_relatorio_pdf
from services.projeto_service import (
    salvar_projeto, buscar_projeto_por_id,
    listar_projetos, deletar_projeto,
)

router    = APIRouter(tags=["Pivô"])
_executor = ThreadPoolExecutor(max_workers=4)


# ── helpers ───────────────────────────────────────────────────

def resposta_ok(resultado):
    return {"success": True, "resultado": resultado, "erro": None}

def resposta_erro(msg, detalhe=None):
    return {"success": False, "resultado": None, "erro": msg, "detalhe": detalhe}

def validar_entrada(dados):
    for campo in ["lamina_mm_dia", "horas_trabalho_dia", "giro_graus"]:
        if not dados.get(campo):
            raise HTTPException(400, f"{campo} não informado")
    if dados.get("area_irrigada_ha") is None and dados.get("raio_m") is None:
        raise HTTPException(400, "Informe área ou raio")
    if dados.get("pressao_pivo_mca", 0) <= 0:
        raise HTTPException(400, "Pressão do pivô inválida")
    if dados.get("horas_trabalho_dia", 0) <= 0:
        raise HTTPException(400, "Horas inválidas")


async def _salvar_bg(user_id: str, dados: dict, resultado: dict):
    """
    Salva projeto em background via thread pool.
    Fire-and-forget: nunca bloqueia a resposta ao usuário.
    Se o banco estiver indisponível, loga e segue em frente.
    """
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(_executor, salvar_projeto, user_id, dados, resultado)
    except Exception:
        print("⚠️  Banco indisponível — projeto não salvo (simulação não afetada)")
        traceback.print_exc()


# ── SIMULAÇÃO ─────────────────────────────────────────────────

@router.post("/simular")
async def simular_pivo(
    payload: Dict,
    user_id: str = Depends(get_current_user)
):
    try:
        dados = payload.copy()
        dados.setdefault("desnivel_succao", 0)
        dados.setdefault("desnivel_recalque", 0)
        dados.setdefault("distancia_captacao_ate_centro", 100)
        dados.setdefault("eficiencia", 0.72)
        dados.setdefault("pressao_pivo_mca", 25)

        validar_entrada(dados)

        if "geometria" in dados and not isinstance(dados["geometria"], dict):
            try:
                dados["geometria"] = json.loads(dados["geometria"])
            except Exception:
                raise HTTPException(400, "Geometria inválida")

        # dimensionamento em thread pool — não bloqueia o event loop
        loop      = asyncio.get_event_loop()
        resultado = await loop.run_in_executor(_executor, dimensionar, dados)

        vazao = (
            resultado.get("vazao_real_m3h")
            or resultado.get("vazao_projeto_m3h")
            or resultado.get("vazao_m3h")
            or 0
        )
        if vazao <= 0:
            return resposta_erro("Sistema inconsistente",
                                 "Sistema não gerou vazão válida")

        # salva em background — resposta ao usuário NÃO espera o banco
        asyncio.create_task(_salvar_bg(user_id, dados, resultado))

        return resposta_ok(resultado)

    except HTTPException as e:
        return resposta_erro(e.detail)
    except Exception as e:
        traceback.print_exc()
        return resposta_erro("Erro interno no processamento", str(e))


# ── OTIMIZAÇÃO ────────────────────────────────────────────────

@router.post("/otimizar")
async def otimizar_pivo(
    payload: Dict,
    user_id: str = Depends(get_current_user)
):
    try:
        from app.services.otimizacao_service import otimizar_projeto
        loop      = asyncio.get_event_loop()
        resultado = await loop.run_in_executor(_executor, otimizar_projeto, payload)
        return resposta_ok(resultado)
    except Exception as e:
        traceback.print_exc()
        return resposta_erro("Erro na otimização", str(e))


# ── PDF ───────────────────────────────────────────────────────

@router.post("/relatorio")
async def gerar_relatorio(
    data: Dict,
    user_id: str = Depends(get_current_user)
):
    try:
        loop    = asyncio.get_event_loop()
        caminho = await loop.run_in_executor(_executor, gerar_relatorio_pdf, data)
        return FileResponse(caminho, media_type="application/pdf",
                            filename="relatorio.pdf")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Erro ao gerar PDF: {str(e)}")


# ── LISTAR ────────────────────────────────────────────────────

@router.get("/listar")
async def listar_todos(user_id: str = Depends(get_current_user)):
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(_executor, listar_projetos, user_id)
    except Exception:
        return []    # banco indisponível → lista vazia, não quebra o frontend


# ── CONSULTAR ────────────────────────────────────────────────

@router.get("/{projeto_id}")
async def obter_projeto(
    projeto_id: str,
    user_id: str = Depends(get_current_user)
):
    loop    = asyncio.get_event_loop()
    projeto = await loop.run_in_executor(_executor, buscar_projeto_por_id, projeto_id)
    if not projeto:
        raise HTTPException(404, "Projeto não encontrado")
    try:
        if isinstance(projeto.get("geometria"), str):
            projeto["geometria"] = json.loads(projeto["geometria"])
        if isinstance(projeto.get("dados_entrada"), str):
            projeto["dados_entrada"] = json.loads(projeto["dados_entrada"])
    except Exception:
        pass
    return projeto


# ── DELETE ────────────────────────────────────────────────────

@router.delete("/{projeto_id}")
async def deletar(
    projeto_id: str,
    user_id: str = Depends(get_current_user)
):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, deletar_projeto, projeto_id, user_id)
    return {"success": True}
