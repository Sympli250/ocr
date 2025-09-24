"""Tests unitaires pour la configuration PaddleOCR."""

from __future__ import annotations

import importlib
import sys
import types
from typing import Iterator

import pytest


class _TrackingPaddleOCR:
    """Capture les paramètres passés au constructeur."""

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    def ocr(self, *args, **kwargs):  # pragma: no cover - non utilisé ici
        raise NotImplementedError


@pytest.fixture()
def app_module(monkeypatch: pytest.MonkeyPatch) -> Iterator[types.ModuleType]:
    """Charge le module `app` avec une implémentation simulée de PaddleOCR."""

    fake_paddleocr = types.ModuleType("paddleocr")
    fake_paddleocr.PaddleOCR = _TrackingPaddleOCR
    fake_paddleocr.__version__ = "test"
    monkeypatch.setitem(sys.modules, "paddleocr", fake_paddleocr)

    module = importlib.import_module("app")
    module = importlib.reload(module)
    yield module

    monkeypatch.delitem(sys.modules, "paddleocr", raising=False)
    sys.modules.pop("app", None)


def test_get_ocr_engine_uses_profile_configuration(app_module: types.ModuleType) -> None:
    engine = app_module.get_ocr_engine("printed")

    assert isinstance(engine, _TrackingPaddleOCR)
    assert engine.kwargs["lang"] == "fr"
    assert engine.kwargs["use_angle_cls"] is True
