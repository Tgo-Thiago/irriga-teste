from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"])


def hash_senha(senha: str):
    return pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str):
    return pwd_context.verify(senha, senha_hash)


def criar_token(user_id: str):

    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
