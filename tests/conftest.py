"""Fixtures compartilhadas da suíte AURA."""

from __future__ import annotations

import os

import pytest

from aura.client import login
from aura.golden import carregar


@pytest.fixture(scope="session")
def golden() -> dict:
    """Golden dataset carregado de data/golden.json."""
    return carregar()


@pytest.fixture(scope="session")
def live_token() -> str:
    """Token para testes marcados como `live`.

    Pula se as credenciais do grupo não estiverem no ambiente.
    """
    usuario = os.environ.get("AURA_USUARIO")
    senha = os.environ.get("AURA_SENHA")
    if not usuario or not senha:
        pytest.skip("AURA_USUARIO/AURA_SENHA não definidos — teste live pulado")
    return login(usuario, senha)
