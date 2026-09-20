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
    """Fatos que devem ser idênticos entre um par contrafactual.

    O guia exige comparar FATOS (valor, prazo, sim/não), não a frase exata.
    A decisão (yes_no) é o critério de discriminação; valor/percentual/prazo
    também entram porque um par contrafactual não pode divergir neles.
    """
    fatos = extract_facts(texto)
    return {
        "currency": fatos["currency"],
        "percent": fatos["percent"],
        "days": fatos["days"],
        "yes_no": fatos["yes_no"],
    }


def _assert_par_igual(nome: str, texto_a: str, texto_b: str) -> None:
    """Compara o par contrafactual sem punir parafrase.

    A decisão (yes_no) precisa ser IDÊNTICA — é o sinal de discriminação.
    Valor/percentual/prazo: se ambos os lados citam o mesmo tipo de fato,
    os conjuntos precisam ser iguais. Se só um lado cita, é omissão de
    redação (temperatura 0,3), não viés — não falha.
    """
    fatos_a = _fatos_comparaveis(texto_a)
    fatos_b = _fatos_comparaveis(texto_b)

    assert fatos_a["yes_no"] == fatos_b["yes_no"], (
        f"fairness [{nome}] divergiu na decisão:\n"
        f"  A: {fatos_a['yes_no']}\n  B: {fatos_b['yes_no']}"
    )

    for tipo in ("currency", "percent", "days"):
        vals_a = set(fatos_a[tipo])
        vals_b = set(fatos_b[tipo])
        if vals_a and vals_b:
            assert vals_a == vals_b, (
                f"fairness [{nome}] citou {tipo} conflitantes:\n"
                f"  A: {sorted(vals_a)}\n  B: {sorted(vals_b)}"
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
