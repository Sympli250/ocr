import importlib
import io
import sys
import types
from pathlib import Path

import pytest
from fastapi import HTTPException
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import Image
from starlette.datastructures import Headers, UploadFile


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class _DummyPaddleOCR:
    def __init__(self, *args, **kwargs):
        pass


@pytest.fixture(scope="module")
def app_module():
    monkeypatch = pytest.MonkeyPatch()
    fake_paddleocr = types.ModuleType("paddleocr")
    fake_paddleocr.PaddleOCR = _DummyPaddleOCR
    fake_paddleocr.__version__ = "test"
    monkeypatch.setitem(sys.modules, "paddleocr", fake_paddleocr)

    module = importlib.import_module("app")

    yield module

    monkeypatch.undo()
    sys.modules.pop("app", None)


def create_png_bytes() -> bytes:
    image = Image.new("RGB", (10, 10), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_pdf_conversion_missing_dependencies(app_module, monkeypatch):
    def fake_convert_from_bytes(*args, **kwargs):
        raise PDFInfoNotInstalledError("Poppler not installed")

    monkeypatch.setattr(app_module, "convert_from_bytes", fake_convert_from_bytes)

    pdf_bytes = b"%PDF-1.4 test"

    with pytest.raises(HTTPException) as exc_info:
        app_module.convert_bytes_to_images(pdf_bytes)

    assert exc_info.value.status_code == 503
    assert "Conversion PDF impossible" in exc_info.value.detail


def test_pdf_conversion_fallback_to_image(app_module, monkeypatch):
    def fake_convert_from_bytes(*args, **kwargs):
        raise ValueError("generic pdf error")

    monkeypatch.setattr(app_module, "convert_from_bytes", fake_convert_from_bytes)

    png_bytes = create_png_bytes()

    images = app_module.convert_bytes_to_images(png_bytes)

    assert len(images) == 1
    assert isinstance(images[0], Image.Image)


def test_validate_file_accepts_pdf_without_extension(app_module):
    pdf_bytes = b"%PDF-1.4 minimal"
    headers = Headers({"content-type": "application/pdf"})
    upload = UploadFile(filename="document", file=io.BytesIO(pdf_bytes), headers=headers)

    try:
        app_module.validate_file(upload, pdf_bytes)
    except HTTPException as exc:
        pytest.fail(f"validate_file should accept valid PDF without extension: {exc}")
