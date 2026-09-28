"""Motor de análise de risco da GuardIA.

Calcula um score de 0 a 100 a partir do contexto da transação PIX.
Faixas: baixo (< 30), médio (30-49) e alto (>= 50). Só o nível "alto"
dispara a intervenção proativa da GuardIA.
"""

import json
from pathlib import Path

import pandas as pd

PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"

PESOS = {
    "valor": 30,
    "horario": 25,
    "chamada": 40,
    "destinatario": 15,
}

LIMITE_VALOR_ALTO = 1000.0   # usado quando não há média histórica do cliente
FATOR_VALOR_HABITUAL = 5     # valor > 5x o valor habitual (mediana das saídas) é atípico
LIMITE_MEDIO = 30
LIMITE_ALTO = 50


def carregar_perfil_cliente() -> dict:
    """Lê perfil_investidor.json e transacoes.csv e devolve o padrão do cliente.

    valor_habitual = mediana das saídas (robusta a gastos pontuais como o aluguel).
    Se os arquivos não existirem, devolve valores padrão e o motor usa o limite fixo.
    """
    perfil = {"nome": "Cliente", "renda_mensal": None, "valor_habitual": None}
    try:
        with open(PASTA_DADOS / "perfil_investidor.json", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        perfil["nome"] = dados.get("nome", perfil["nome"])
        perfil["renda_mensal"] = dados.get("renda_mensal")
    except (OSError, ValueError):
        pass
    try:
        transacoes = pd.read_csv(PASTA_DADOS / "transacoes.csv")
        saidas = transacoes.loc[transacoes["tipo"] == "saida", "valor"]
        if not saidas.empty:
            perfil["valor_habitual"] = float(saidas.median())
    except (OSError, ValueError, KeyError):
        pass
    return perfil


def calcular_score_risco(
    valor: float,
    chave_destino: str,
    chamada_ativa: bool,
    hora_atual: int,
    valor_habitual: float | None = None,
) -> dict:
    """Avalia o risco de uma transação PIX.

    valor_habitual: valor típico das saídas do cliente (ver carregar_perfil_cliente).
    Quando informado, o valor é comparado com o padrão do próprio cliente;
    caso contrário, usa o limite fixo LIMITE_VALOR_ALTO.
    """
    score = 0
    fatores = []

    # Regra 1: valor elevado / fora do padrão do cliente
    if valor_habitual and valor_habitual > 0:
        if valor > FATOR_VALOR_HABITUAL * valor_habitual:
            score += PESOS["valor"]
            fatores.append(
                f"Valor (R$ {valor:.2f}) muito acima do padrão do cliente (habitual: R$ {valor_habitual:.2f})"
            )
    elif valor > LIMITE_VALOR_ALTO:
        score += PESOS["valor"]
        fatores.append(f"Valor elevado (R$ {valor:.2f})")

    # Regra 2: horário noturno atípico (22h às 6h)
    if hora_atual >= 22 or hora_atual < 6:
        score += PESOS["horario"]
        fatores.append("Transação em horário noturno atípico")

    # Regra 3: ligação telefônica ativa durante a operação (sinal clássico de engenharia social)
    if chamada_ativa:
        score += PESOS["chamada"]
        fatores.append("Ligação telefônica ativa detectada no dispositivo")

    # Regra 4: destinatário novo / não salvo (simulado pelo prefixo "nova_")
    if chave_destino.strip().lower().startswith("nova_"):
        score += PESOS["destinatario"]
        fatores.append("Destinatário recente ou não salvo na agenda")

    score = min(score, 100)

    if score >= LIMITE_ALTO:
        nivel = "alto"
    elif score >= LIMITE_MEDIO:
        nivel = "médio"
    else:
        nivel = "baixo"

    return {
        "score": score,
        "nivel": nivel,
        "suspeita": nivel == "alto",
        "fatores": fatores,
        "valor": valor,
    }
