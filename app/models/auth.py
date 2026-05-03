from pydantic import BaseModel, EmailStr


# =========================================================
# REQUESTS
# =========================================================

class SignupRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


# =========================================================
# RESPONSES (opcional, mas já profissionaliza)
# =========================================================

class SignupResponse(BaseModel):
    user_id: str
    message: str


class LoginResponse(BaseModel):
    token: str
    user_id: str


    