from fastapi import APIRouter, HTTPException
from models.auth import (
    SignupRequest,
    LoginRequest,
    SignupResponse,
    LoginResponse
)

from app.services.auth_service import (
    hash_senha,
    verificar_senha,
    criar_token
)

from app.services.user_service import (
    criar_usuario,
    buscar_usuario_por_email
)


router = APIRouter(tags=["Auth"])


# =========================================================
# SIGNUP
# =========================================================
@router.post("/signup", response_model=SignupResponse)
def signup(data: SignupRequest):

    # Verifica se já existe
    existente = buscar_usuario_por_email(data.email)

    if existente:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    # Criptografa senha
    senha_hash = hash_senha(data.senha)

    # Cria usuário
    user_id = criar_usuario(
        nome=data.nome,
        email=data.email,
        senha_hash=senha_hash
    )

    return SignupResponse(
        user_id=user_id,
        message="Usuário criado com sucesso"
    )


# =========================================================
# LOGIN
# =========================================================
@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):

    user = buscar_usuario_por_email(data.email)

    if not user:
        raise HTTPException(status_code=401, detail="Usuário inválido")

    if not verificar_senha(data.senha, user["senha_hash"]):
        raise HTTPException(status_code=401, detail="Senha inválida")

    token = criar_token(user["id"])

    return LoginResponse(
        token=token,
        user_id=user["id"]
    )
