"""Golden dataset: perguntas + fatos esperados + respostas gravadas.

Formato do JSON (versão 1):

```json
{
  "version": 1,
  "collected_at": "2025-09-20T12:00:00-03:00",
  "cases": [
    {
      "id": "anuidade_padrao",
      "pergunta": "Qual é a anuidade do cartão de crédito?",
      "fatos": {
        "currency": [240.0],
        "percent": [],
        "days": [],
        "yes_no": null,
        "sources": ["tarifas-cartao.md"]
      },
      "resposta": {"message": "...", "sources": ["tarifas-cartao.md"]}
    }
  ]
}
```

A suíte normal roda contra `resposta` (gravação). Testes marcados `live`
batem no sistema no ar e comparam com `fatos`.
"""

from __future__ import annotations

import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "data" / "golden.json"


def carregar(caminho: Path | None = None) -> dict:
    caminho = caminho or GOLDEN_PATH
    if not caminho.exists():
        raise FileNotFoundError(
            f"Golden dataset não encontrado: {caminho}. "
            "Rode `python -m aura.record_golden` primeiro."
        )
    return json.loads(caminho.read_text(encoding="utf-8"))


def salvar(dados: dict, caminho: Path | None = None) -> None:
    caminho = caminho or GOLDEN_PATH
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def casos(dados: dict) -> list[dict]:
    return dados["cases"]
