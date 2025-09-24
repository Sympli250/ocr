# 🔤 Symplissime OCR API

API OCR robuste et optimisée avec PaddleOCR pour traitement de documents et images.

## 📋 Corrections Apportées

### 🐛 BUGS CORRIGÉS

#### Lot 1: Gestion d'erreurs et fuites de ressources
- ✅ **Fuite mémoire critique** : Gestionnaire de contexte pour fichiers temporaires
- ✅ **Gestion d'erreurs** : Exceptions spécifiques avec messages détaillés
- ✅ **Validation fichiers** : Vérification type MIME et taille (50MB max)
- ✅ **Limites de sécurité** : Protection contre les gros fichiers

#### Lot 2: Robustesse OCR et traitement d'images
- ✅ **Résultats OCR NULL** : Vérification complète des structures de données
- ✅ **Images corrompues** : Validation d'intégrité avec verify()
- ✅ **Initialisation multiple** : Cache des moteurs OCR (lazy loading)
- ✅ **Performance** : Traitement optimisé des pages multiples

#### Lot 3: Configuration et profils OCR
- ✅ **Profil handwriting** : Correction langue FR au lieu de EN
- ✅ **Profil multilang** : Amélioration configuration multilingue
- ✅ **Paramètres OCR** : Optimisation par type de document
- ✅ **Seuils détection** : Ajustement par profil (legal, scanned, etc.)

### 🚀 NOUVELLES FONCTIONNALITÉS

#### Monitoring et Observabilité
- ✅ **Health Check** : `/health` endpoint pour monitoring
- ✅ **Logs structurés** : Logging détaillé avec niveaux
- ✅ **Métriques** : Temps de traitement, lignes détectées
- ✅ **Métadonnées** : Informations complètes dans les réponses

#### Performance et UX
- ✅ **Cache OCR** : Initialisation paresseuse des moteurs
- ✅ **CORS** : Support cross-origin pour frontends
- ✅ **Confiance OCR** : Score de confiance par ligne détectée
- ✅ **Format HTML amélioré** : Interface responsive avec CSS

#### Configuration et Déploiement
- ✅ **Variables environnement** : Configuration via .env
- ✅ **Script de démarrage** : `start.py` avec vérifications
- ✅ **Tests automatisés** : `test_api.py` complet
- ✅ **Documentation** : README détaillé

## 🚀 Démarrage Rapide

### Installation
```bash
# Installation automatique
python start.py

# Ou manuel
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Utilisation Windows
```cmd
# Double-clic sur go.bat ou :
go.bat
```

### Test de l'API
```bash
python test_api.py
```

## 📚 Documentation API

### Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/health` | GET | Statut de l'API |
| `/ocr` | POST | Traitement OCR |
| `/docs` | GET | Documentation Swagger |

### Profils OCR

| Profil API | Nom Français | Description | Langue | Usage |
|------------|--------------|-------------|---------|-------|
| `printed` | **📄 Imprimé** | Texte imprimé standard | FR | Documents classiques |
| `handwriting` | **✍️ Manuscrit** | Écriture manuscrite | FR | Notes manuscrites |
| `legal` | **⚖️ Juridique** | Documents juridiques | FR | Contrats, actes |
| `scanned` | **🖨️ Scanné** | Documents scannés | FR | Scans de qualité variable |
| `english` | **🇬🇧 Anglais** | Texte anglais | EN | Documents en anglais |
| `multilang` | **🌍 Multilingue** | Multi-langues | FR | Documents mixtes |

### Améliorations d'image

- `contrast` : Améliore le contraste
- `sharpness` : Améliore la netteté
- `brightness` : Ajuste la luminosité
- `defloutage` : Réduit le flou

### Formats de sortie

- `json` : Format structuré avec métadonnées
- `html` : Page web formatée
- `text` : Texte brut

## 📊 Exemple d'utilisation

### cURL
```bash
curl -X POST "http://localhost:8000/ocr" \
  -F "file=@document.pdf" \
  -F "profile=juridique" \
  -F "output_format=json" \
  -F "enhance=contrast"
```

### Python
```python
import requests

files = {'file': open('document.pdf', 'rb')}
params = {
    'profile': 'imprime',  # ou 'manuscrit', 'juridique', etc.
    'output_format': 'json',
    'enhance': 'contrast'
}

response = requests.post('http://localhost:8000/ocr',
                        files=files, params=params)
result = response.json()
```

## 📈 Performance

- **Temps de traitement** : ~2-5s par page selon complexité
- **Formats supportés** : PDF, PNG, JPG, TIFF, BMP, WEBP
- **Taille limite** : 50MB par fichier
- **Pages maximum** : 100 par document

## 🔧 Configuration Avancée

Créer un fichier `.env` :
```env
HOST=0.0.0.0
PORT=8000
MAX_FILE_SIZE=52428800
MAX_PAGES=100
LOG_LEVEL=info
```

## 🧪 Tests

Le script `test_api.py` effectue :
- ✅ Tests de tous les profils OCR
- ✅ Tests de tous les formats de sortie
- ✅ Tests de gestion d'erreurs
- ✅ Tests de performance
- ✅ Validation de l'API complète

## 📝 Changements Techniques

### Avant (Bugs)
```python
# Fuite mémoire
temp = tempfile.NamedTemporaryFile(delete=False)
# ... traitement ...
# Fichier jamais supprimé !

# Crash potentiel
for line in ocr_result[0]:  # [0] peut être None
```

### Après (Corrigé)
```python
# Gestion sécurisée
@contextmanager
def temporary_file(suffix=".png"):
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        yield temp_file
    finally:
        if temp_file:
            os.remove(temp_file.name)

# Vérifications robustes
if ocr_result and ocr_result[0]:
    for line in ocr_result[0]:
        if line and len(line) >= 2:
```

## 🎨 Interface Utilisateur

### Affichage Coloré avec Rich
L'API utilise désormais **Rich** pour un affichage console moderne :
- 🎨 **Bannière colorée** au démarrage
- 📊 **Tableaux formatés** pour les statuts
- 🌈 **Messages colorés** par type (succès/erreur/info)
- ⏳ **Barres de progression** pour les installations
- 📈 **Métriques visuelles** dans les tests

### Scripts d'Interface
- **`start.py`** : Démarrage avec interface colorée
- **`test_api.py`** : Tests avec barres de progression
- **`test_paddleocr.py`** : Diagnostic avec statut coloré
- **`install_rich.py`** : Installation automatique Rich

## 🎯 Version

**v1.1.0** - Sécurité maximale + Architecture moderne

### Nouveautés v1.1.0
- ✅ **6 bugs critiques** corrigés (XSS, validation, sécurité)
- ✅ **Architecture Pydantic** (types sûrs, validation auto)
- ✅ **Logging avancé** (fichiers logs, traçabilité, debug)
- ✅ **Compatibilité PaddleOCR** (détection version, fallbacks)
- ✅ **Interface Rich moderne** (bannières colorées, progress bars)
- ✅ **Sécurité renforcée** (protection XSS, validation stricte)

---
*🎨 **Symplissime OCR v1.1.0** - Réalisé par Ayi NEDJIMI Consultants*