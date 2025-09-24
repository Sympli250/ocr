"""Tests unitaires ciblés pour l'API FastAPI."""

from __future__ import annotations

import importlib
import io
import sys
import types
from typing import Iterator, Tuple

import pytest
from fastapi.testclient import TestClient


class _DummyPaddleOCR:
    """Implémentation minimale utilisée pour les tests."""

    def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - signature imposée
        pass


@pytest.fixture()
def test_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[Tuple[TestClient, types.ModuleType]]:
    """Retourne un client de test avec PaddleOCR simulé."""

    fake_paddleocr = types.ModuleType("paddleocr")
    fake_paddleocr.PaddleOCR = _DummyPaddleOCR
    fake_paddleocr.__version__ = "test"
    monkeypatch.setitem(sys.modules, "paddleocr", fake_paddleocr)

    module = importlib.import_module("app")
    module = importlib.reload(module)

    with TestClient(module.app) as client:
        yield client, module

    monkeypatch.delitem(sys.modules, "paddleocr", raising=False)
    sys.modules.pop("app", None)


def test_health_check_reports_healthy(test_client: Tuple[TestClient, types.ModuleType]) -> None:
    client, _ = test_client

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["paddleocr_working"] is True


def test_error_handling_empty_file(test_client: Tuple[TestClient, types.ModuleType]) -> None:
    client, _ = test_client

    response = client.post(
        "/ocr",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    assert "Type de fichier non supporté" in response.json()["detail"]


def test_error_handling_invalid_profile(test_client: Tuple[TestClient, types.ModuleType]) -> None:
    client, _ = test_client

    png = io.BytesIO()
    png.write(b"fake")
    png.seek(0)

    response = client.post(
        "/ocr",
        params={"profile": "invalid_profile"},
        files={"file": ("test.png", png, "image/png")},
    )

    assert response.status_code == 422
