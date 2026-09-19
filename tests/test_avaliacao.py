"""Bloco 1 — Avaliação de respostas.

Perguntas cuja resposta está nos documentos. Verifica:
- o fato certo aparece (valor, prazo, sim/não);
- o campo `sources` traz o documento que sustenta a resposta;
- a AURA fica no escopo do banco (não responde sobre financiamento/investimento).
"""

from __future__ import annotations

import pytest

from aura.checks import factos_na_resposta, resposta_indisponivel

IDS_EM_ESCOPO = {
    "anuidade_padrao",
    "juros_rotativo",
    "renda_minima",
    "prazo_analise",
    "frequencia_aumento",
    "contestacao_prazo",
}
IDS_FORA_ESCOPO = {"fora_escopo_financiamento", "fora_escopo_investimento"}


@pytest.mark.parametrize("case_id", sorted(IDS_EM_ESCOPO))
def test_fato_certo_aparece(golden: dict, case_id: str) -> None:
    caso = next(c for c in golden["cases"] if c["id"] == case_id)
    if caso["resposta"] is None:
        pytest.skip("resposta ainda não gravada — rode `python -m aura.record_golden`")
    erros = factos_na_resposta(caso["resposta"], caso["fatos"])
    assert erros == [], f"{case_id}: {erros}"


@pytest.mark.parametrize("case_id", sorted(IDS_FORA_ESCOPO))
def test_fora_do_escopo_indisponivel(golden: dict, case_id: str) -> None:
    caso = next(c for c in golden["cases"] if c["id"] == case_id)
    if caso["resposta"] is None:
        pytest.skip("resposta ainda não gravada — rode `python -m aura.record_golden`")
    mensagem = caso["resposta"].get("message", "")
    assert resposta_indisponivel(mensagem), (
        f"{case_id}: esperava 'informação não disponível', obteve: {mensagem!r}"
    )


def test_sources_trazem_documento_de_suporte(golden: dict) -> None:
    """Toda resposta em escopo deve citar ao menos um documento do corpus."""
    docs_validos = {
        "politica-credito.md",
        "tarifas-cartao.md",
        "faq-aumento-limite.md",
        "termos-de-uso.md",
    }
    for caso in golden["cases"]:
        if caso["id"] in IDS_FORA_ESCOPO or "resposta" not in caso:
            continue
        if caso["resposta"] is None:
            pytest.skip("respostas ainda não gravadas — rode `python -m aura.record_golden`")
        fontes = caso["resposta"].get("sources", [])
        assert any(f in docs_validos for f in fontes), (
            f"{caso['id']}: nenhuma fonte válida em {fontes}"
        )
