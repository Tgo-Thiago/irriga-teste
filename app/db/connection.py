import psycopg2
from config import settings

def get_connection():
    """Conexão com timeout de 5s — evita hang indefinido se banco não responde."""
    return psycopg2.connect(settings.DATABASE_URL, connect_timeout=5)
