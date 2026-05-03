def calcular_cu(perfil):
    if not perfil:
        return 0

    # 🔥 filtra valores válidos
    pressoes = [p["pressao_mca"] for p in perfil if p.get("pressao_mca", 0) > 0]

    if len(pressoes) < 2:
        return 0

    media = sum(pressoes) / len(pressoes)

    if media == 0:
        return 0

    desvios = [abs(p - media) for p in pressoes]

    cu = 100 * (1 - sum(desvios) / (len(pressoes) * media))

    return round(max(0, cu), 2)


def calcular_du(perfil):
    if not perfil:
        return 0

    # 🔥 filtra valores válidos
    pressoes = [p["pressao_mca"] for p in perfil if p.get("pressao_mca", 0) > 0]

    n = len(pressoes)

    if n < 4:
        return 0  # poucos pontos → DU não confiável

    pressoes.sort()

    # 🔥 garante pelo menos 1 elemento no quartil
    q = max(1, int(n * 0.25))

    media_total = sum(pressoes) / n

    if media_total == 0:
        return 0

    media_baixa = sum(pressoes[:q]) / q

    du = (media_baixa / media_total) * 100

    return round(max(0, du), 2)