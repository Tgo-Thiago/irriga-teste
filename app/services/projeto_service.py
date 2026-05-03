import json
from app.db.connection import get_connection


def salvar_projeto(user_id: str, dados: dict, resultado: dict):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO projetos (user_id, dados_entrada, resultado)
            VALUES (%s, %s, %s) RETURNING id
        """, (user_id, json.dumps(dados), json.dumps(resultado)))
        projeto_id = cur.fetchone()[0]
        conn.commit()
        return str(projeto_id)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def buscar_projeto_por_id(projeto_id: str):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT id, user_id, dados_entrada, resultado, created_at
            FROM projetos WHERE id = %s
        """, (projeto_id,))
        row = cur.fetchone()
        if not row:
            return None
        dados, resultado = row[2], row[3]
        try:
            if isinstance(dados, str):     dados     = json.loads(dados)
        except Exception: pass
        try:
            if isinstance(resultado, str): resultado = json.loads(resultado)
        except Exception: pass
        return {
            "id": str(row[0]), "user_id": str(row[1]),
            "dados_entrada": dados, "resultado": resultado,
            "geometria": dados.get("geometria") if isinstance(dados, dict) else None,
            "created_at": str(row[4]),
        }
    finally:
        cur.close()
        conn.close()


def listar_projetos(user_id: str):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT id, dados_entrada, resultado, created_at
            FROM projetos WHERE user_id = %s ORDER BY created_at DESC
        """, (user_id,))
        projetos = []
        for row in cur.fetchall():
            dados, resultado = row[1], row[2]
            try:
                if isinstance(dados, str):     dados     = json.loads(dados)
            except Exception: pass
            try:
                if isinstance(resultado, str): resultado = json.loads(resultado)
            except Exception: pass
            projetos.append({
                "id": str(row[0]), "dados_entrada": dados, "resultado": resultado,
                "geometria": dados.get("geometria") if isinstance(dados, dict) else None,
                "created_at": str(row[3]),
            })
        return projetos
    finally:
        cur.close()
        conn.close()


def deletar_projeto(projeto_id: str, user_id: str):
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM projetos WHERE id = %s AND user_id = %s",
                    (projeto_id, user_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
