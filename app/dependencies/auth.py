from fastapi import Header, HTTPException
from jose import jwt
from app.config import settings


def get_current_user(authorization: str = Header(None)):

    if not authorization:
        raise HTTPException(401, "Token não informado")

    try:
        token = authorization.replace("Bearer ", "")

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        return payload["sub"]

    except Exception:
        raise HTTPException(401, "Token inválido")