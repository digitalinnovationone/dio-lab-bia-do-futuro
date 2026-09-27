import io
import json
from urllib import error

import pytest

from invest_ai.adapters import OllamaGatewayError, OllamaLlmGateway


class RespostaHttpFake:
    """Resposta HTTP mínima para testar o adaptador sem acessar o Ollama real."""

    def __init__(self, payload):
        self._conteudo = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self._conteudo


def test_gateway_envia_schema_think_false_e_temperature_zero(monkeypatch):
    capturado = {}

    def urlopen_fake(requisicao, timeout):
        capturado["timeout"] = timeout
        capturado["payload"] = json.loads(requisicao.data.decode("utf-8"))
        return RespostaHttpFake(
            {
                "response": json.dumps(
                    {
                        "available_capital": 500,
                        "objective": "INCOME",
                        "risk_tolerance": "LOW",
                        "investment_horizon_months": None,
                        "liquidity_need": None,
                        "periodic_income": True,
                        "income_frequency": "MONTHLY",
                        "experience_level": None,
                        "restrictions": [],
                    }
                )
            }
        )

    monkeypatch.setattr(
        "invest_ai.adapters.ollama_llm_gateway.request.urlopen",
        urlopen_fake,
    )

    resultado = OllamaLlmGateway(timeout_seconds=15).interpretar_necessidade(
        "Tenho R$ 500 e quero renda mensal com baixo risco."
    )

    assert capturado["timeout"] == 15
    assert capturado["payload"]["model"] == "qwen3:4b"
    assert capturado["payload"]["think"] is False
    assert capturado["payload"]["stream"] is False
    assert capturado["payload"]["options"]["temperature"] == 0
    assert capturado["payload"]["format"]["additionalProperties"] is False
    assert resultado["available_capital"] == 500
    assert resultado["objective"] == "INCOME"


def test_gateway_preserva_utf8_no_prompt(monkeypatch):
    capturado = {}

    def urlopen_fake(requisicao, timeout):
        capturado["payload"] = json.loads(requisicao.data.decode("utf-8"))
        return RespostaHttpFake({"response": "{}"})

    monkeypatch.setattr(
        "invest_ai.adapters.ollama_llm_gateway.request.urlopen",
        urlopen_fake,
    )

    OllamaLlmGateway().interpretar_necessidade(
        "Quero segurança e não quero perder liquidez."
    )

    prompt = capturado["payload"]["prompt"]
    assert "segurança" in prompt
    assert "não quero perder liquidez" in prompt


def test_gateway_falha_de_forma_controlada_quando_ollama_esta_indisponivel(monkeypatch):
    def urlopen_fake(requisicao, timeout):
        raise error.URLError("conexão recusada")

    monkeypatch.setattr(
        "invest_ai.adapters.ollama_llm_gateway.request.urlopen",
        urlopen_fake,
    )

    with pytest.raises(OllamaGatewayError, match="conectar ao Ollama"):
        OllamaLlmGateway().interpretar_necessidade("Tenho R$ 500.")


def test_gateway_falha_de_forma_controlada_em_erro_http(monkeypatch):
    def urlopen_fake(requisicao, timeout):
        raise error.HTTPError(
            url="http://localhost:11434/api/generate",
            code=500,
            msg="erro",
            hdrs=None,
            fp=io.BytesIO(b"erro"),
        )

    monkeypatch.setattr(
        "invest_ai.adapters.ollama_llm_gateway.request.urlopen",
        urlopen_fake,
    )

    with pytest.raises(OllamaGatewayError, match="erro HTTP 500"):
        OllamaLlmGateway().interpretar_necessidade("Tenho R$ 500.")


def test_gateway_rejeita_envelope_http_sem_json(monkeypatch):
    class RespostaInvalida:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return b"nao-json"

    monkeypatch.setattr(
        "invest_ai.adapters.ollama_llm_gateway.request.urlopen",
        lambda requisicao, timeout: RespostaInvalida(),
    )

    with pytest.raises(OllamaGatewayError, match="não contém JSON válido"):
        OllamaLlmGateway().interpretar_necessidade("Tenho R$ 500.")


def test_gateway_rejeita_conteudo_estruturado_sem_json(monkeypatch):
    monkeypatch.setattr(
        "invest_ai.adapters.ollama_llm_gateway.request.urlopen",
        lambda requisicao, timeout: RespostaHttpFake({"response": "texto livre"}),
    )

    with pytest.raises(OllamaGatewayError, match="não é JSON válido"):
        OllamaLlmGateway().interpretar_necessidade("Tenho R$ 500.")


def test_gateway_rejeita_conteudo_estruturado_que_nao_seja_objeto(monkeypatch):
    monkeypatch.setattr(
        "invest_ai.adapters.ollama_llm_gateway.request.urlopen",
        lambda requisicao, timeout: RespostaHttpFake({"response": "[]"}),
    )

    with pytest.raises(OllamaGatewayError, match="objeto JSON"):
        OllamaLlmGateway().interpretar_necessidade("Tenho R$ 500.")
