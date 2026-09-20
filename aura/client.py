"""Cliente mínimo da API da AURA (sistema no ar).

Regras respeitadas (guia da Trilha 2):
- timeout de 180 s (servidor hiberna; primeira chamada pode passar de 2 min);
- login separado do chat (token expira em 30 min);
- `200` pode ser erro de infraestrutura — tratado como falha, não como conteúdo.
"""

from __future__ import annotations

import json
import os

import requests

BASE = os.environ.get("AURA_BASE", "https://assistente-financeiro-testes.onrender.com")
TIMEOUT = 180

# Mensagens que indicam falha de infraestrutura/LLM, NÃO resposta da AURA.
# Inclui vazamento de instruções do prompt: quando o template de saída
# ("Strict JSON output", "Avatar state valid", etc.) volta no lugar da
# resposta, não é conteúdo — é o sistema quebrando o contrato.
INFRA_MARKERS = (
    "Cota da API do provedor de IA esgotada",
    "Ocorreu um erro ao processar sua mensagem",
    "Ops, demorei demais para responder",
    "Strict JSON output",
    "Valid Output",
    "Avatar state valid",
    "Movement valid",
    "hallucination outside RAG context",
)


class AuraError(RuntimeError):
    """Erro de infraestrutura/transporte — não é resposta da AURA."""


def login(usuario: str, senha: str) -> str:
    r = requests.post(
        f"{BASE}/auth/login",
        json={"username": usuario, "password": senha},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def chat(token: str, pergunta: str, history: list | None = None) -> dict:
    """Faz uma pergunta ao `/chat` e devolve o payload `data` com a resposta.

    Levanta `AuraError` se a resposta for falha de infraestrutura (cota,
    erro interno, demora) ou se o stream terminar sem mensagem.
    """
    r = requests.post(
        f"{BASE}/chat",
        json={"message": pergunta, "history": history or []},
        headers={"Authorization": f"Bearer {token}"},
        stream=True,
        timeout=TIMEOUT,
    )
    r.raise_for_status()

    for linha in r.iter_lines(decode_unicode=True):
        if not linha or not linha.startswith("data:"):
            continue
        dados = json.loads(linha[len("data:"):].strip())
        if "message" in dados:
            return dados

    raise AuraError("stream terminou sem resposta")


def perguntar(token: str, pergunta: str, history: list | None = None) -> dict:
    """`chat` com detecção de respostas de infraestrutura."""
    dados = chat(token, pergunta, history=history)
    mensagem = dados.get("message", "")
    for marcador in INFRA_MARKERS:
        if marcador in mensagem:
            raise AuraError(f"falha de infraestrutura detectada: {marcador!r}")
    return dados
