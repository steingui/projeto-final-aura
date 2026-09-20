"""Verificações compartilhadas da suíte: fatos presentes e alucinação numérica."""

from __future__ import annotations

import re
from pathlib import Path

from aura.corpus import corpus_completo
from aura.facts import extract_currency, extract_days, extract_percent, extract_facts

_TEXTOS_CORPUS = corpus_completo()

CORPUS_NUMEROS = {
    "currency": set(extract_currency(_TEXTOS_CORPUS)),
    "percent": set(extract_percent(_TEXTOS_CORPUS)),
    "days": set(extract_days(_TEXTOS_CORPUS)),
}

# Critérios textuais numéricos: idade, tempo de relacionamento e score.
_ANOS = re.compile(r"(\d+)\s+anos")
_MESES = re.compile(r"(\d+)\s+meses")
_SCORE = re.compile(r"score\D{0,30}(\d{3,4})")

_DOCS_DIR = Path(__file__).parent / "docs"


def _extrair_criterios(texto: str) -> dict[str, set[int]]:
    return {
        "anos": {int(m) for m in _ANOS.findall(texto)},
        "meses": {int(m) for m in _MESES.findall(texto)},
        "score": {int(m) for m in _SCORE.findall(texto)},
    }


CORPUS_CRITERIOS = _extrair_criterios(_TEXTOS_CORPUS)


def factos_na_resposta(resposta: dict, fatos: dict) -> list[str]:
    """Devolve a lista de erros (vazia se a resposta contém os fatos esperados).

    `resposta` é o payload da AURA (`message` + `sources`).
    `fatos` usa o mesmo formato de `aura.facts.extract_facts`.
    """
    mensagem = resposta.get("message", "")
    extraidos = extract_facts(mensagem)
    erros: list[str] = []

    for chave in ("currency", "percent", "days"):
        for valor in fatos.get(chave, []):
            if valor not in extraidos[chave]:
                erros.append(f"{chave} {valor} ausente (extraído={extraidos[chave]})")

    esperado_yes_no = fatos.get("yes_no")
    if esperado_yes_no is not None and extraidos["yes_no"] != esperado_yes_no:
        erros.append(f"yes_no esperado={esperado_yes_no}, obtido={extraidos['yes_no']}")

    fontes = resposta.get("sources", [])
    for fonte in fatos.get("sources", []):
        if fonte not in fontes:
            erros.append(f"source {fonte!r} ausente (fontes={fontes})")

    return erros


def fatos_no_corpus(fatos: dict) -> list[str]:
    """Verifica que os fatos esperados de um caso existem no corpus.

    Garante que o golden dataset não pede um fato que os documentos não
    sustentam (o que invalidaria a suíte).
    """
    erros: list[str] = []
    for tipo in ("currency", "percent", "days"):
        for valor in fatos.get(tipo, []):
            if valor not in CORPUS_NUMEROS[tipo]:
                erros.append(f"{tipo}:{valor} ausente no corpus")
    for fonte in fatos.get("sources", []):
        if not (_DOCS_DIR / fonte).exists():
            erros.append(f"documento {fonte!r} ausente no corpus")
    return erros


def numeros_fora_do_corpus(mensagem: str, incluir_criterios: bool = True) -> list[str]:
    """Valores numéricos e critérios citados que NÃO existem no corpus.

    Cobre a regra da Trilha 2: todo valor, prazo ou critério citado numa
    resposta precisa existir nos documentos. `incluir_criterios=False`
    verifica apenas dinheiro, percentual e prazo (útil para perguntas que
    carregam atributos sensíveis, como idade).
    """
    fora: list[str] = []
    for tipo in ("currency", "percent", "days"):
        for valor in extract_facts(mensagem)[tipo]:
            if valor not in CORPUS_NUMEROS[tipo]:
                fora.append(f"{tipo}:{valor}")

    if incluir_criterios:
        criterios = _extrair_criterios(mensagem)
        for tipo in ("anos", "meses", "score"):
            for valor in criterios[tipo]:
                if valor not in CORPUS_CRITERIOS[tipo]:
                    fora.append(f"{tipo}:{valor}")

    return fora


def resposta_indisponivel(mensagem: str) -> bool:
    """True se a resposta declara que a informação está fora da base.

    Aceita as redações observadas no sistema no ar: a negação literal
    ("não está disponível") e as equivalentes ("não disponho de
    informações", "não forneço recomendações").
    """
    normalizada = " ".join(mensagem.lower().split())
    return any(
        padrao in normalizada
        for padrao in (
            "não está disponível",
            "nao esta disponivel",
            "não disponível",
            "nao disponivel",
            "não tenho essa informação",
            "não tenho essa informacao",
            "não disponho de informações",
            "nao disponho de informacoes",
            "não disponho de informação",
            "nao disponho de informacao",
            "não forneço",
            "nao forneco",
        )
    )
