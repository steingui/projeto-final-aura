"""Extração de fatos de respostas em texto livre.

O LLM roda com temperatura 0,3: a mesma pergunta pode voltar com outra
redação. Estes extratores convertem a resposta em fatos comparáveis
(valor, percentual, prazo, sim/não, fontes).
"""

from __future__ import annotations

import json
import re

_MOEDA = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)")
_PERCENT = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
_DIAS = re.compile(r"(\d+)\s+dias")


def extract_currency(texto: str) -> list[float]:
    """Todos os valores em R$ citados no texto, em ordem de aparição."""
    valores: list[float] = []
    for match in _MOEDA.finditer(texto):
        bruto = match.group(1).replace(".", "").replace(",", ".")
        valores.append(float(bruto))
    return valores


def extract_percent(texto: str) -> list[float]:
    """Todos os percentuais citados, em ordem de aparição."""
    return [float(m.replace(",", ".")) for m in _PERCENT.findall(texto)]


def extract_days(texto: str) -> list[int]:
    """Todos os prazos em dias citados, em ordem de aparição."""
    return [int(m) for m in _DIAS.findall(texto)]


def extract_yes_no(texto: str) -> bool | None:
    """Sim -> True, Não -> False, indeterminado -> None.

    Heurística pragmática: decide pela PRIMEIRA ocorrência explícita de
    "sim"/"não" no texto. A resposta típica abre com o veredito
    ("Sim, você pode..."); o "não" de "não influencia" vem depois e não
    pode inverter a decisão.
    """
    t = texto.lower()
    sim = re.search(r"\bsim\b", t)
    nao = re.search(r"\bnão\b|\bnao\b", t)
    if sim and (nao is None or sim.start() < nao.start()):
        return True
    if nao:
        return False
    return None


def extract_sources(texto: str) -> list[str]:
    """Extrai a lista de documentos citados como fontes.

    Aceita dois formatos observados no sistema:
      - `Sources: ["tarifas-cartao.md"]`
      - `["tarifas-cartao.md"]` puro
    """
    t = texto.strip()
    match = re.search(r"\[[^\]]*\]", t)
    if not match:
        return []
    try:
        dados = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    if isinstance(dados, list):
        return [s for s in dados if isinstance(s, str)]
    return []


def extract_facts(texto: str) -> dict:
    """Pacote de fatos extraídos de uma resposta, pronto para comparação."""
    return {
        "currency": extract_currency(texto),
        "percent": extract_percent(texto),
        "days": extract_days(texto),
        "yes_no": extract_yes_no(texto),
        "sources": extract_sources(texto),
    }
