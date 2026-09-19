"""Bloco 4 — Regressão de prompts (golden dataset).

A suíte normal roda contra a gravação (`data/golden.json`). A marcação
`live` bate no sistema no ar para detectar mudança de comportamento
(regressão de prompt/modelo).

Antes de comparar respostas, valida que o próprio golden dataset é
consistente: os fatos esperados precisam existir no corpus.
"""

from __future__ import annotations

import pytest

from aura.checks import factos_na_resposta, fatos_no_corpus
from aura.client import perguntar
from aura.golden import carregar, casos


def _ids_com_fatos() -> list[str]:
    """Só os casos com `fatos` + `resposta` (exclui pares de fairness)."""
    return [c["id"] for c in casos(carregar()) if "fatos" in c]


def test_golden_dataset_estrutura(golden: dict) -> None:
    assert golden["version"] == 1
    assert len(golden["cases"]) >= 6


@pytest.mark.parametrize("case_id", _ids_com_fatos())
def test_golden_fatos_existem_no_corpus(golden: dict, case_id: str) -> None:
    """O golden não pode pedir um fato que os documentos não sustentam."""
    caso = next(c for c in golden["cases"] if c["id"] == case_id)
    erros = fatos_no_corpus(caso["fatos"])
    assert erros == [], f"{case_id}: {erros}"


@pytest.mark.parametrize("case_id", _ids_com_fatos())
def test_regressao_contra_gravacao(golden: dict, case_id: str) -> None:
    """Roda offline: a gravação deve continuar satisfazendo os fatos esperados."""
    caso = next(c for c in golden["cases"] if c["id"] == case_id)
    if caso["resposta"] is None:
        pytest.skip("resposta ainda não gravada — rode `python -m aura.record_golden`")
    erros = factos_na_resposta(caso["resposta"], caso["fatos"])
    assert erros == [], f"{case_id}: {erros}"


@pytest.mark.live
@pytest.mark.parametrize("case_id", _ids_com_fatos())
def test_regressao_live(live_token: str, golden: dict, case_id: str) -> None:
    """Contra o sistema no ar: a resposta de hoje deve manter os fatos esperados."""
    caso = next(c for c in golden["cases"] if c["id"] == case_id)
    resposta = perguntar(live_token, caso["pergunta"])
    erros = factos_na_resposta(resposta, caso["fatos"])
    assert erros == [], f"{case_id}: {erros}"
