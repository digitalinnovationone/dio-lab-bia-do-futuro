"""Adaptador local do Ollama para interpretação de necessidades.

O adaptador usa somente a API HTTP local do Ollama e solicita saída
estruturada por JSON Schema. A responsabilidade do modelo permanece limitada
à extração semântica da mensagem da pessoa usuária.
"""

import json
from typing import Any
from urllib import error, request


class OllamaGatewayError(RuntimeError):
    """Indica falha controlada na comunicação ou resposta do Ollama."""


class OllamaLlmGateway:
    """Implementa a porta de LLM usando a API local do Ollama."""

    _SCHEMA = {
        "type": "object",
        "properties": {
            "available_capital": {"type": ["number", "null"]},
            "objective": {
                "type": ["string", "null"],
                "enum": ["INCOME", "GROWTH", "PRESERVATION", None],
            },
            "risk_tolerance": {
                "type": ["string", "null"],
                "enum": ["LOW", "MEDIUM", "HIGH", None],
            },
            "investment_horizon_months": {"type": ["integer", "null"]},
            "liquidity_need": {"type": ["string", "null"]},
            "periodic_income": {"type": ["boolean", "null"]},
            "income_frequency": {
                "type": ["string", "null"],
                "enum": ["MONTHLY", "OTHER", None],
            },
            "experience_level": {"type": ["string", "null"]},
            "restrictions": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": [
            "available_capital",
            "objective",
            "risk_tolerance",
            "investment_horizon_months",
            "liquidity_need",
            "periodic_income",
            "income_frequency",
            "experience_level",
            "restrictions",
        ],
        "additionalProperties": False,
    }

    def __init__(
        self,
        model: str = "qwen3:4b",
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 60.0,
    ) -> None:
        self._model = model
        self._endpoint = base_url.rstrip("/") + "/api/generate"
        self._timeout_seconds = timeout_seconds

    def interpretar_necessidade(self, mensagem: str) -> dict[str, Any]:
        payload = {
            "model": self._model,
            "prompt": self._criar_prompt(mensagem),
            "stream": False,
            "think": False,
            "format": self._SCHEMA,
            "options": {"temperature": 0},
        }
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        requisicao = request.Request(
            self._endpoint,
            data=corpo,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )

        try:
            with request.urlopen(
                requisicao,
                timeout=self._timeout_seconds,
            ) as resposta:
                resposta_http = resposta.read().decode("utf-8")
        except error.HTTPError as exc:
            raise OllamaGatewayError(
                f"O Ollama respondeu com erro HTTP {exc.code}."
            ) from exc
        except error.URLError as exc:
            raise OllamaGatewayError(
                "Não foi possível conectar ao Ollama local."
            ) from exc
        except TimeoutError as exc:
            raise OllamaGatewayError(
                "O Ollama excedeu o tempo limite da requisição."
            ) from exc

        try:
            envelope = json.loads(resposta_http)
        except json.JSONDecodeError as exc:
            raise OllamaGatewayError(
                "O Ollama retornou uma resposta HTTP que não contém JSON válido."
            ) from exc

        conteudo = envelope.get("response")
        if not isinstance(conteudo, str):
            raise OllamaGatewayError(
                "A resposta do Ollama não contém o campo textual esperado."
            )

        try:
            interpretacao = json.loads(conteudo)
        except json.JSONDecodeError as exc:
            raise OllamaGatewayError(
                "O conteúdo estruturado retornado pelo Ollama não é JSON válido."
            ) from exc

        if not isinstance(interpretacao, dict):
            raise OllamaGatewayError(
                "O conteúdo estruturado do Ollama deve ser um objeto JSON."
            )

        return interpretacao

    @staticmethod
    def _criar_prompt(mensagem: str) -> str:
        return f"""Você é um extrator de necessidades de investimento.

Extraia somente informações presentes ou diretamente expressas pela mensagem.

Regras:
- available_capital: valor numérico disponível para investir, sem símbolo de moeda.
- objective: INCOME para geração de renda, GROWTH para crescimento patrimonial e PRESERVATION para preservação de capital.
- risk_tolerance: LOW, MEDIUM ou HIGH somente quando a preferência estiver expressa.
- investment_horizon_months: horizonte explicitamente informado, convertido para meses quando possível sem estimativa.
- liquidity_need: preserve de forma curta somente uma necessidade de liquidez explicitamente informada.
- periodic_income: true quando houver desejo explícito de renda periódica; false somente quando houver recusa explícita; caso contrário, null.
- income_frequency: MONTHLY para renda mensal; OTHER para outra frequência explícita; caso contrário, null.
- experience_level: preserve de forma curta somente quando a experiência for explicitamente informada.
- restrictions: liste somente restrições explicitamente informadas; use lista vazia quando não houver.
- Não recomende ativos.
- Não produza ticker, preço, rendimento, indicador financeiro ou previsão.
- Não crie informações ausentes.

Mensagem da pessoa usuária:
{json.dumps(mensagem, ensure_ascii=False)}
"""
