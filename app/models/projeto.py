# app/models/projeto.py
from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime
from typing import Optional

class ProjetoPivoDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    dados_entrada: dict
    resultado: dict
    criado_em: datetime = Field(default_factory=datetime.utcnow)
