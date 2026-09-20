"""Bloco 3 — Fairness (pares contrafactuais).

A mesma pergunta, trocando apenas um atributo sensível (gênero, idade,
raça, religião, estado civil, deficiência, região). Os fatos extraídos das
duas respostas precisam ser iguais.

- Offline: roda contra os pares gravados no golden dataset.
- Live (`-m live`): bate no sistema no ar com os pares do golden.
"""

from __future__ import annotations

import pytest

from aura.client import perguntar
from aura.facts import extract_facts


def _fatos_comparaveis(texto: str) -> dict:
    """Sinal de decisão que deve ser idêntico entre um par contrafactual.

    Fairness se mede pela DECISÃO (sim/não), não pela redação: o LLM roda
    com temperatura 0,3 e parafraseia a resposta, então a mesma pergunta
    pode citar "90 dias" numa versão e omitir na outra. O que não pode
    mudar é o veredito para o cliente.
    """
    return {"yes_no": extract_facts(texto)["yes_no"]}


def _assert_par_igual(nome: str, texto_a: str, texto_b: str) -> None:
    fatos_a = _fatos_comparaveis(texto_a)
    fatos_b = _fatos_comparaveis(texto_b)
    assert fatos_a == fatos_b, (
        f"fairness [{nome}] divergiu:\n  A: {fatos_a}\n  B: {fatos_b}"
    )


def _pares_do_golden(golden: dict) -> list[dict]:
    return [c for c in golden["cases"] if c.get("type") == "fairness"]


def test_golden_tem_pares_fairness(golden: dict) -> None:
    assert len(_pares_do_golden(golden)) >= 3


@pytest.mark.parametrize(
    "case_id",
    [c["id"] for c in _pares_do_golden(__import__("aura.golden", fromlist=["carregar"]).carregar())],
)
def test_fairness_contra_gravacao(golden: dict, case_id: str) -> None:
    """Offline: os fatos do par gravado devem ser idênticos."""
    caso = next(c for c in golden["cases"] if c["id"] == case_id)
    if caso.get("resposta_a") is None or caso.get("resposta_b") is None:
        pytest.skip("par ainda não gravado — rode `python -m aura.record_golden`")
    _assert_par_igual(
        caso["id"],
        caso["resposta_a"].get("message", ""),
        caso["resposta_b"].get("message", ""),
    )


@pytest.mark.live
@pytest.mark.parametrize(
    "case_id",
    [c["id"] for c in _pares_do_golden(__import__("aura.golden", fromlist=["carregar"]).carregar())],
)
def test_fairness_live(live_token: str, golden: dict, case_id: str) -> None:
    """Contra o sistema no ar. Rode com `-m live` e as credenciais no ambiente."""
    caso = next(c for c in golden["cases"] if c["id"] == case_id)
    resp_a = perguntar(live_token, caso["pergunta_a"])["message"]
    resp_b = perguntar(live_token, caso["pergunta_b"])["message"]
    _assert_par_igual(caso["id"], resp_a, resp_b)
