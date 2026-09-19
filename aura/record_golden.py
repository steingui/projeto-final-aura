"""Grava o golden dataset contra o sistema AURA no ar.

Uso:
    AURA_USUARIO=grupo01 AURA_SENHA=... python -m aura.record_golden

Lê `data/golden.json` (fonte única de perguntas e fatos esperados), chama o
`/chat` para cada caso e grava as respostas reais de volta no arquivo. Rode
UMA vez — a cota do LLM é dividida pela turma inteira. Respeita o limite de
20 chamadas/min espaçando as chamadas com sleep de 5 s.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from aura.client import login, perguntar
from aura.golden import carregar, salvar


def main() -> None:
    usuario = os.environ["AURA_USUARIO"]
    senha = os.environ["AURA_SENHA"]
    token = login(usuario, senha)

    dados = carregar()
    for caso in dados["cases"]:
        if caso.get("type") == "fairness":
            caso["resposta_a"] = perguntar(token, caso["pergunta_a"])
            time.sleep(5)
            caso["resposta_b"] = perguntar(token, caso["pergunta_b"])
        else:
            caso["resposta"] = perguntar(token, caso["pergunta"])
        print(f"[ok] {caso['id']}")
        time.sleep(5)

    dados["collected_at"] = datetime.now(timezone.utc).isoformat()
    salvar(dados)
    print("Golden dataset gravado em data/golden.json")


if __name__ == "__main__":
    main()
