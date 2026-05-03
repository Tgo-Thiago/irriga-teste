from app.db.connection import get_connection


def criar_usuario(nome, email, senha_hash):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (nome, email, senha_hash)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (nome, email, senha_hash))

    user_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return str(user_id)


def buscar_usuario_por_email(email):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nome, email, senha_hash
        FROM users
        WHERE email = %s
    """, (email,))

    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        return None

    return {
        "id": str(user[0]),
        "nome": user[1],
        "email": user[2],
        "senha_hash": user[3]
    }