from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR
from pdf2image import convert_from_bytes
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)
from PIL import Image, ImageEnhance, ImageFilter
import tempfile
import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Union
from pathlib import Path
import mimetypes
from contextlib import contextmanager
import html
import io
from pydantic import BaseModel, Field, validator
from enum import Enum
import sys
import traceback
import imghdr

# Configuration du logging détaillé
class DetailedFormatter(logging.Formatter):
    def format(self, record):
        # Ajout d'informations contextuelles
        if hasattr(record, 'request_id'):
            record.msg = f"[{record.request_id}] {record.msg}"
        return super().format(record)

# Configuration logging avec handler personnalisé
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ocr_api.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Modèles Pydantic pour validation
class OCRProfile(str, Enum):
    IMPRIME = "printed"
    MANUSCRIT = "handwriting"
    JURIDIQUE = "legal"
    SCANNE = "scanned"
    ANGLAIS = "english"
    MULTILINGUE = "multilang"

class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    HTML = "html"

class Enhancement(str, Enum):
    CONTRAST = "contrast"
    SHARPNESS = "sharpness"
    BRIGHTNESS = "brightness"
    DEFLOUTAGE = "defloutage"

class OCRLine(BaseModel):
    text: str = Field(..., description="Texte OCR détecté")
    bbox: List[List[float]] = Field(default_factory=list, description="Coordonnées de la boîte englobante")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Score de confiance")

class OCRPageResult(BaseModel):
    page: int = Field(..., gt=0, description="Numéro de page")
    lines: List[OCRLine] = Field(default_factory=list, description="Lignes détectées")
    status: str = Field(default="success", description="Statut du traitement")
    error: Optional[str] = Field(default=None, description="Message d'erreur si applicable")

class OCRMetadata(BaseModel):
    filename: str = Field(..., description="Nom du fichier traité")
    profile: OCRProfile = Field(..., description="Profil OCR utilisé")
    enhancement: Optional[Enhancement] = Field(default=None, description="Amélioration appliquée")
    processing_time: float = Field(..., ge=0, description="Temps de traitement en secondes")
    total_pages: int = Field(..., ge=0, description="Nombre total de pages")
    total_lines: int = Field(..., ge=0, description="Nombre total de lignes détectées")

class OCRResponse(BaseModel):
    status: str = Field(default="success", description="Statut de la réponse")
    results: List[OCRPageResult] = Field(..., description="Résultats OCR par page")
    metadata: OCRMetadata = Field(..., description="Métadonnées du traitement")

app = FastAPI(
    title="Symplissime OCR API",
    description="API OCR multi-profils avec PaddleOCR et pré-traitement d'images",
    version="1.1.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/tiff', 'image/bmp', 'image/webp',
    'application/pdf'
}
MAX_PAGES = 100

# Pool de threads pour traitement parallèle
executor = ThreadPoolExecutor(max_workers=4)

# Configuration des profils OCR - compatibilité PaddleOCR v3.2.0+
OCR_PROFILE_CONFIGS = {
    "printed": {"use_angle_cls": True, "lang": "fr", "show_log": False},
    "handwriting": {"use_angle_cls": True, "lang": "fr", "det_db_thresh": 0.2, "show_log": False},
    "legal": {"use_angle_cls": True, "lang": "fr", "det_db_thresh": 0.3, "show_log": False},
    "scanned": {"use_angle_cls": True, "lang": "fr", "det_db_box_thresh": 0.5, "show_log": False},
    "english": {"use_angle_cls": True, "lang": "en", "show_log": False},
    "multilang": {"use_angle_cls": True, "lang": "fr", "show_log": False}
}

# Cache des moteurs OCR initialisés
ocr_engines_cache: Dict[str, PaddleOCR] = {}

def check_paddleocr_compatibility():
    """Vérifie la compatibilité de PaddleOCR - ERREURS EXPLICITES"""
    try:
        from paddleocr import PaddleOCR
        import paddleocr

        # Version de PaddleOCR
        version = getattr(paddleocr, '__version__', 'unknown')
        logger.info(f"Version PaddleOCR détectée: {version}")

        # Test d'initialisation basique (compatible v3.2.0+)
        test_ocr = PaddleOCR(lang="fr")
        logger.info("Test d'initialisation PaddleOCR réussi")

        return True
    except ImportError as e:
        logger.error(f"PaddleOCR NON INSTALLÉ: {e}")
        raise ImportError(f"PaddleOCR requis. Installez avec: pip install paddleocr")
    except Exception as e:
        logger.error(f"ERREUR PaddleOCR: {e}")
        raise Exception(f"Problème PaddleOCR: {e}")


def get_ocr_engine(profile: str) -> PaddleOCR:
    """Obtient ou initialise un moteur OCR pour le profil donné"""
    if profile not in ocr_engines_cache:
        if profile not in OCR_PROFILE_CONFIGS:
            raise HTTPException(
                status_code=400,
                detail=f"Profil OCR non supporté: {profile}"
            )

        logger.info(f"Initialisation du moteur OCR pour le profil: {profile}")
        config = OCR_PROFILE_CONFIGS[profile].copy()

        try:
            # Import et initialisation directe de PaddleOCR
            from paddleocr import PaddleOCR
            ocr_engines_cache[profile] = PaddleOCR(**config)
            logger.info(f"Moteur OCR '{profile}' initialisé avec succès")

        except ImportError as import_error:
            logger.error(f"PaddleOCR non installé: {import_error}")
            raise HTTPException(
                status_code=500,
                detail=f"PaddleOCR non installé. Installez avec: pip install paddleocr"
            )

        except Exception as e:
            logger.error(f"Erreur initialisation OCR '{profile}': {e}")
            logger.error(f"Stack trace: {traceback.format_exc()}")

            # UN SEUL fallback: Configuration ultra-minimale
            try:
                minimal_config = {
                    "lang": config.get("lang", "fr"),
                    "use_angle_cls": config.get("use_angle_cls", False),
                    "show_log": False,
                }
                from paddleocr import PaddleOCR
                ocr_engines_cache[profile] = PaddleOCR(**minimal_config)
                logger.warning(f"Fallback réussi pour '{profile}' avec config ultra-minimale")
            except Exception as minimal_error:
                logger.error(f"Fallback échec pour '{profile}': {minimal_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Impossible d'initialiser PaddleOCR pour '{profile}'. Erreur: {str(e)}. Fallback: {str(minimal_error)}"
                )

    return ocr_engines_cache[profile]

@contextmanager
def temporary_file(suffix: str = ".png"):
    """Gestionnaire de contexte pour fichiers temporaires"""
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        yield temp_file
    finally:
        if temp_file:
            temp_file.close()
            try:
                os.remove(temp_file.name)
            except OSError as e:
                logger.warning(f"Impossible de supprimer le fichier temporaire {temp_file.name}: {e}")

def validate_file(file: UploadFile, file_bytes: Optional[bytes] = None) -> None:
    """Valide le fichier uploadé"""
    # Vérification du type MIME avec différentes sources
    guessed_mime, _ = mimetypes.guess_type(file.filename or "")
    candidate_mime_types = set(filter(None, [guessed_mime]))

    content_type = getattr(file, "content_type", None)
    if content_type:
        candidate_mime_types.add(content_type)

    if file_bytes is not None:
        if file_bytes.startswith(b"%PDF-"):
            candidate_mime_types.add("application/pdf")
        else:
            detected_image_format = imghdr.what(None, h=file_bytes)
            image_mime_map = {
                "jpeg": "image/jpeg",
                "png": "image/png",
                "tiff": "image/tiff",
                "bmp": "image/bmp",
                "webp": "image/webp",
            }
            if detected_image_format:
                mapped_mime = image_mime_map.get(detected_image_format)
                if mapped_mime:
                    candidate_mime_types.add(mapped_mime)

    if not candidate_mime_types.intersection(ALLOWED_MIME_TYPES):
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporté. Types autorisés: {', '.join(ALLOWED_MIME_TYPES)}"
        )

    # Vérification de la taille réelle après lecture si disponible
    if file_bytes is not None:
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier trop volumineux. Taille maximale: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
    # Sinon, vérification approximative avec file.size
    elif hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux. Taille maximale: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

def preprocess_image(img: Image.Image, enhance: Optional[str] = None) -> Image.Image:
    """Pré-traitement des images avec gestion d'erreurs"""
    try:
        if not enhance:
            return img

        # Conversion en RGB si nécessaire
        if img.mode != 'RGB':
            img = img.convert('RGB')

        if enhance == "contrast":
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
        elif enhance == "sharpness":
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(2.0)
        elif enhance == "brightness":
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.5)
        elif enhance == "defloutage":
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150))

        return img
    except Exception as e:
        logger.warning(f"Échec du pré-traitement '{enhance}': {e}")
        return img  # Retourne l'image originale en cas d'erreur

def convert_bytes_to_images(file_bytes: bytes) -> List[Image.Image]:
    """Convertit les bytes en images avec gestion d'erreurs robuste"""
    images = []

    try:
        # Tentative de conversion PDF avec pdf2image
        images = convert_from_bytes(file_bytes, dpi=200, fmt='PNG')
        logger.info(f"PDF converti en {len(images)} page(s)")
    except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError) as pdf_dependency_error:
        logger.error(
            "Échec critique conversion PDF: %s. Dépendances manquantes ou PDF invalide.",
            pdf_dependency_error,
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Conversion PDF impossible côté serveur. "
                "Vérifiez l'installation des dépendances (ex: poppler)."
            ),
        ) from pdf_dependency_error
    except Exception as pdf_error:
        logger.info(f"Échec conversion PDF: {pdf_error}. Tentative image directe.")
        try:
            # Tentative d'ouverture directe depuis les bytes (sans fichier temporaire)
            img_bytes = io.BytesIO(file_bytes)
            img = Image.open(img_bytes)
            # Vérification de l'intégrité de l'image en créant une copie
            img_copy = img.copy()
            img_copy.verify()
            # Utilisation de l'image originale (non fermée par verify)
            images = [img]
            logger.info("Image directe ouverte avec succès")
        except Exception as img_error:
            logger.error(f"Échec ouverture image: {img_error}")
            raise HTTPException(
                status_code=400,
                detail=f"Format de fichier non supporté. Erreurs: PDF={str(pdf_error)[:100]}, Image={str(img_error)[:100]}"
            )

    if len(images) > MAX_PAGES:
        logger.warning(f"Document avec {len(images)} pages, limité à {MAX_PAGES}")
        images = images[:MAX_PAGES]

    return images

def process_single_page(args) -> Dict:
    """Traite une seule page pour traitement parallèle"""
    page_num, img, enhance, ocr_engine = args

    try:
        # Pré-traitement si demandé
        if enhance:
            img = preprocess_image(img, enhance)

        # Sauvegarde temporaire pour OCR
        with temporary_file(".png") as temp_file:
            img.save(
                temp_file.name,
                format="PNG",  # optimize=True n'est pas supporté pour PNG
            )
            use_cls = getattr(ocr_engine, "use_angle_cls", False)
            ocr_result = ocr_engine.ocr(temp_file.name, cls=use_cls)

        # Traitement des résultats OCR avec vérifications robustes
        page_lines = []
        if ocr_result and ocr_result[0]:  # Vérification que le résultat n'est pas None ou vide
            for line in ocr_result[0]:
                try:
                    # Vérifications complètes de la structure OCR
                    if (line and len(line) >= 2 and
                        line[1] and isinstance(line[1], (list, tuple)) and
                        len(line[1]) >= 1):

                        # Extraction sécurisée du texte et de la confiance
                        text = str(line[1][0]) if line[1][0] is not None else ""
                        confidence = float(line[1][1]) if len(line[1]) > 1 and isinstance(line[1][1], (int, float)) else 0.0
                        bbox = line[0] if line[0] and isinstance(line[0], (list, tuple)) else []

                        page_lines.append({
                            "text": text,
                            "bbox": bbox,
                            "confidence": confidence
                        })
                except (TypeError, IndexError, ValueError) as e:
                    logger.warning(f"Format OCR inattendu pour une ligne: {e} - Ligne ignorée")
                    continue

        return {
            "page": page_num,
            "lines": page_lines,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Échec traitement page {page_num}: {e}")
        return {
            "page": page_num,
            "lines": [],
            "status": "error",
            "error": str(e)
        }

async def run_ocr(ocr_engine: PaddleOCR, file_bytes: bytes, enhance: Optional[str] = None) -> List[Dict]:
    """Exécute l'OCR avec traitement parallèle et gestion d'erreurs robuste"""
    try:
        # Conversion en images
        images = convert_bytes_to_images(file_bytes)

        if not images:
            raise HTTPException(status_code=400, detail="Aucune image valide trouvée")

        # Préparation des arguments pour traitement parallèle
        args_list = [(page_num, img, enhance, ocr_engine) for page_num, img in enumerate(images, start=1)]

        # Traitement des pages (séquentiel pour éviter les conflits de ressources)
        # Le traitement parallèle vrai nécessiterait des moteurs OCR séparés
        results = []
        for args in args_list:
            result = process_single_page(args)
            results.append(result)

        # Tri des résultats par numéro de page
        results.sort(key=lambda x: x["page"])

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Échec général OCR: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@app.get("/health")
async def health_check():
    """Point de contrôle de santé de l'API"""
    try:
        from paddleocr import PaddleOCR
        import paddleocr
        version = getattr(paddleocr, '__version__', 'unknown')

        # Test rapide
        test = PaddleOCR(lang="fr")
        paddleocr_status = True
        error_msg = None
    except ImportError as e:
        paddleocr_status = False
        version = "non installé"
        error_msg = f"PaddleOCR non installé: {str(e)}"
    except Exception as e:
        paddleocr_status = False
        version = "erreur"
        error_msg = f"Erreur PaddleOCR: {str(e)}"

    status = "healthy" if paddleocr_status else "degraded"

    return {
        "status": status,
        "version": "1.1.0",
        "profiles": list(OCR_PROFILE_CONFIGS.keys()),
        "paddleocr_version": version,
        "paddleocr_working": paddleocr_status,
        "error": error_msg
    }

@app.post("/ocr", response_model=OCRResponse)
async def ocr_document(
    file: UploadFile = File(..., description="Fichier à traiter (PDF, PNG, JPG, etc.)"),
    profile: OCRProfile = Query(OCRProfile.IMPRIME, description="Profil OCR à utiliser"),
    output_format: OutputFormat = Query(OutputFormat.TEXT, description="Format de sortie"),
    enhance: Optional[Enhancement] = Query(None, description="Amélioration d'image optionnelle")
):
    """Endpoint principal pour traitement OCR"""
    start_time = asyncio.get_running_loop().time()

    try:
        # Logging détaillé avec ID de requête
        import uuid
        request_id = str(uuid.uuid4())[:8]

        # Validation préliminaire du fichier
        validate_file(file)
        logger.info(f"[{request_id}] Début traitement OCR - Fichier: {file.filename}, Profil: {profile.value}")

        # Lecture des données
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Fichier vide")

        # Validation finale avec taille réelle
        validate_file(file, file_bytes)
        logger.debug(f"[{request_id}] Fichier validé - Taille: {len(file_bytes)} bytes")

        # Obtention du moteur OCR
        ocr_engine = get_ocr_engine(profile.value)

        # Traitement OCR
        enhance_value = enhance.value if enhance else None
        results = await run_ocr(ocr_engine, file_bytes, enhance_value)

        # Calcul du temps de traitement
        processing_time = asyncio.get_running_loop().time() - start_time
        logger.info(f"[{request_id}] Traitement terminé en {processing_time:.2f}s")

        # Création de la réponse avec Pydantic
        ocr_response = OCRResponse(
            status="success",
            results=[
                OCRPageResult(
                    page=page["page"],
                    lines=[
                        OCRLine(
                            text=line["text"],
                            bbox=line["bbox"],
                            confidence=line["confidence"]
                        ) for line in page["lines"]
                    ],
                    status=page.get("status", "success"),
                    error=page.get("error")
                ) for page in results
            ],
            metadata=OCRMetadata(
                filename=file.filename or "unknown",
                profile=profile,
                enhancement=enhance,
                processing_time=round(processing_time, 2),
                total_pages=len(results),
                total_lines=sum(len(page["lines"]) for page in results)
            )
        )

        if output_format == OutputFormat.JSON:
            return ocr_response

        elif output_format == OutputFormat.HTML:
            html_content = f"""<html>
            <head>
                <meta charset="utf-8">
                <title>Résultat OCR - {file.filename}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .metadata {{ background: #f5f5f5; padding: 10px; margin-bottom: 20px; }}
                    .page {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; }}
                    .line {{ margin: 5px 0; padding: 5px; background: #fafafa; }}
                    .confidence {{ color: #666; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <h1>Résultat OCR</h1>
                <div class="metadata">
                    <strong>Fichier:</strong> {file.filename}<br>
                    <strong>Profil:</strong> {profile.value}<br>
                    <strong>Amélioration:</strong> {enhance.value if enhance else 'Aucune'}<br>
                    <strong>Temps de traitement:</strong> {processing_time:.2f}s<br>
                    <strong>Pages:</strong> {len(results)}<br>
                </div>"""

            for page in results:
                html_content += f'<div class="page"><h2>Page {page["page"]}</h2>'
                if page.get("status") == "error":
                    html_content += f'<p style="color: red;">Erreur: {page.get("error", "Inconnue")}</p>'
                else:
                    for line in page["lines"]:
                        confidence = line.get("confidence", 0)
                        escaped_text = html.escape(line["text"])
                        html_content += f'<div class="line">{escaped_text} '
                        html_content += f'<span class="confidence">(confiance: {confidence:.2f})</span></div>'
                html_content += '</div>'

            html_content += "</body></html>"
            return HTMLResponse(content=html_content)

        else:  # format text
            text_output = f"=== Résultat OCR - {file.filename} ===\n"
            text_output += f"Profil: {profile.value} | Amélioration: {enhance.value if enhance else 'Aucune'} | Temps: {processing_time:.2f}s\n\n"

            for page in results:
                text_output += f"[Page {page['page']}]\n"
                if page.get("status") == "error":
                    text_output += f"ERREUR: {page.get('error', 'Inconnue')}\n"
                else:
                    for line in page["lines"]:
                        text_output += f"{line['text']}\n"
                text_output += "\n"

            return PlainTextResponse(content=text_output)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    logger.info("🚀 Démarrage Symplissime OCR API v1.1.0")
    logger.info(f"📊 Profils OCR disponibles: {list(OCR_PROFILE_CONFIGS.keys())}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
