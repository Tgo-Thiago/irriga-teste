# auth.py
from app.config import settings

def create_token(data: dict):
    secret = settings.JWT_SECRET
    algorithm = settings.JWT_ALGORITHM
    # lógica de criação do token...
