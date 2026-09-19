"""Corpus do Banco Aurora — os fatos canônicos dos quatro documentos.

Fonte de verdade local para a suíte de testes. Os textos são espelhos do
`backend/docs/` do repositório do sistema-alvo (branch `main`).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_DOCS_DIR = Path(__file__).parent / "docs"


def corpus_texto(nome: str) -> str:
    """Lê o texto integral de um documento do corpus."""
    caminho = _DOCS_DIR / nome
    if not caminho.exists():
        raise FileNotFoundError(f"Documento do corpus não encontrado: {nome}")
    return caminho.read_text(encoding="utf-8")


def corpus_completo() -> str:
    """Concatena os quatro documentos, na ordem canônica."""
    docs = [
        "politica-credito.md",
        "tarifas-cartao.md",
        "faq-aumento-limite.md",
        "termos-de-uso.md",
    ]
    return "\n\n".join(corpus_texto(d) for d in docs)


# Fatos canônicos extraídos dos documentos (para os testes de alucinação).
# Cada valor é uma string que DEVE existir no corpus.
FATOS_CANONICOS = {
    "anuidade_padrao": ("R$ 240,00/ano", "tarifas-cartao.md"),
    "anuidade_isenta_condicao": ("gasta acima de R$ 500/mês", "tarifas-cartao.md"),
    "juros_rotativo": ("12,5% ao mês", "tarifas-cartao.md"),
    "juros_parcelamento": ("8,9% ao mês", "tarifas-cartao.md"),
    "saque": ("R$ 12,00 por operação", "tarifas-cartao.md"),
    "iof_internacional": ("5,38%", "tarifas-cartao.md"),
    "renda_minima": ("R$ 1.500,00", "politica-credito.md"),
    "idade_minima": ("18 anos", "politica-credito.md"),
    "prazo_analise": ("5 dias úteis", "politica-credito.md"),
    "frequencia_aumento": ("90 dias", "faq-aumento-limite.md"),
    "recusa_reenvio": ("30 dias", "faq-aumento-limite.md"),
    "contestacao_prazo": ("90 dias", "termos-de-uso.md"),
    "resposta_contestacao": ("10 dias úteis", "termos-de-uso.md"),
    "aviso_alteracao": ("30 dias", "termos-de-uso.md"),
}


def fatos_do_corpus() -> list[dict]:
    """Devolve os fatos canônicos em formato serializável."""
    return [
        {"nome": nome, "valor": valor, "documento": doc}
        for nome, (valor, doc) in FATOS_CANONICOS.items()
    ]


def normalizar(texto: str) -> str:
    """Normaliza texto para comparação: minúsculas, sem acentos, sem espaços duplos."""
    texto = texto.lower().strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def achar_no_corpus(trecho: str) -> bool:
    """True se `trecho` (normalizado) existe em algum documento do corpus."""
    alvo = normalizar(trecho)
    return alvo in normalizar(corpus_completo())


def fatos_seriais_dump() -> str:
    return json.dumps(fatos_do_corpus(), ensure_ascii=False, indent=2)
