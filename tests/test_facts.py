"""Testes da camada de fatos — roda offline, contra o corpus real do Banco Aurora.

Estes testes verificam os extratores que a suíte usa para avaliar as respostas
da AURA. São a fundação dos blocos obrigatórios: se o extrator erra, todo o
resto da suíte erra junto.
"""

import pytest

from aura.facts import (
    extract_currency,
    extract_percent,
    extract_days,
    extract_yes_no,
    extract_sources,
)


# ---------------------------------------------------------------------------
# Moeda (R$)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("A anuidade é R$ 240,00 por ano.", [240.0]),
        ("cobrada em 12x de R$ 20,00 na fatura", [20.0]),
        ("O saque custa R$ 12,00 por operação", [12.0]),
        ("limite inicial de R$ 800", [800.0]),
        ("R$ 1.500,00 de renda mínima", [1500.0]),
        ("R$ 12.000,00", [12000.0]),
        ("não há tarifa", []),
    ],
)
def test_extract_currency(texto: str, esperado) -> None:
    assert extract_currency(texto) == esperado


# ---------------------------------------------------------------------------
# Percentual (%)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("juros do rotativo de 12,5% ao mês", [12.5]),
        ("IOF de 5,38%", [5.38]),
        ("parcelamento de 8,9% ao mês", [8.9]),
        ("não cobramos juros nessa operação", []),
    ],
)
def test_extract_percent(texto: str, esperado) -> None:
    assert extract_percent(texto) == esperado


# ---------------------------------------------------------------------------
# Prazos em dias
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("a análise leva até 5 dias úteis", [5]),
        ("contestação em até 90 dias da fatura", [90]),
        ("uma solicitação a cada 90 dias", [90]),
        ("aviso prévio de 30 dias", [30]),
        ("sem prazo definido aqui", []),
    ],
)
def test_extract_days(texto: str, esperado) -> None:
    assert extract_days(texto) == esperado


# ---------------------------------------------------------------------------
# Sim / Não
# ---------------------------------------------------------------------------
def test_extract_yes_no_positivo() -> None:
    assert extract_yes_no("Sim, o cancelamento é gratuito.") is True


def test_extract_yes_no_negativo() -> None:
    assert extract_yes_no("Não, não há tarifa diferenciada.") is False


def test_extract_yes_no_indefinido() -> None:
    assert extract_yes_no("Isso depende da sua renda.") is None


# ---------------------------------------------------------------------------
# Fontes
# ---------------------------------------------------------------------------
def test_extract_sources_lista() -> None:
    texto = 'Resposta. Sources: ["tarifas-cartao.md", "termos-de-uso.md"]'
    assert extract_sources(texto) == ["tarifas-cartao.md", "termos-de-uso.md"]


def test_extract_sources_json_puro() -> None:
    texto = '["politica-credito.md"]'
    assert extract_sources(texto) == ["politica-credito.md"]


def test_extract_sources_sem_fontes() -> None:
    assert extract_sources("Nenhuma fonte citada.") == []
