"""Bloco 2 — Detecção de alucinação.

- Perguntas fora dos documentos devem receber "essa informação não está
  disponível".
- Todo valor, prazo ou critério citado numa resposta precisa existir nos
  documentos (verificação numérica contra o corpus).
"""

from __future__ import annotations

import pytest

from aura.checks import numeros_fora_do_corpus, resposta_indisponivel

IDS_FORA_ESCOPO = {"fora_escopo_financiamento", "fora_escopo_investimento"}


@pytest.mark.parametrize("case_id", sorted(IDS_FORA_ESCOPO))
def test_fora_do_escopo_nao_inventa(golden: dict, case_id: str) -> None:
    caso = next(c for c in golden["cases"] if c["id"] == case_id)
    if caso["resposta"] is None:
        pytest.skip("resposta ainda não gravada — rode `python -m aura.record_golden`")
    mensagem = caso["resposta"].get("message", "")
    assert resposta_indisponivel(mensagem), (
        f"{case_id}: resposta fora do escopo deveria declarar indisponibilidade: {mensagem!r}"
    )


def _mensagens_do_golden(golden: dict) -> list[tuple[str, str]]:
    """Devolve (case_id, mensagem) para toda resposta gravada no golden."""
    pares: list[tuple[str, str]] = []
    for caso in golden["cases"]:
        if caso.get("type") == "fairness":
            for chave in ("resposta_a", "resposta_b"):
                resposta = caso.get(chave)
                if resposta:
                    pares.append((caso["id"], resposta.get("message", "")))
        elif caso.get("resposta"):
            pares.append((caso["id"], caso["resposta"].get("message", "")))
    return pares


def test_nenhum_valor_numerico_fora_do_corpus(golden: dict) -> None:
    """Nenhuma resposta do golden pode citar valor que não existe no corpus."""
    mensagens = _mensagens_do_golden(golden)
    if not mensagens:
        pytest.skip("respostas ainda não gravadas — rode `python -m aura.record_golden`")
    for case_id, mensagem in mensagens:
        fora = numeros_fora_do_corpus(mensagem)
        assert fora == [], f"{case_id}: valores fora do corpus {fora} em {mensagem!r}"


# ---------------------------------------------------------------------------
# Critérios textuais (score, idade, tempo de relacionamento)
# ---------------------------------------------------------------------------
def test_criterio_score_inventado_e_detectado() -> None:
    mensagem = "A aprovação exige score de crédito acima de 900."
    assert "score:900" in numeros_fora_do_corpus(mensagem)


def test_criterio_idade_inventado_e_detectado() -> None:
    mensagem = "É preciso ter 25 anos para pedir o cartão."
    assert "anos:25" in numeros_fora_do_corpus(mensagem)


def test_criterio_valido_nao_e_sinalizado() -> None:
    mensagem = (
        "É preciso ter 18 anos, e o aumento automático exige score acima de 700 "
        "e 12 meses de relacionamento."
    )
    assert numeros_fora_do_corpus(mensagem) == []
