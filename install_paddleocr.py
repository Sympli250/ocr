#!/usr/bin/env python3
"""
Script d'installation robuste de PaddleOCR
Gère les différents environnements Python (système, utilisateur, venv)
"""
import subprocess
import sys
import os

def run_command(cmd, description=""):
    """Exécute une commande et retourne le succès"""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Succès")
            return True
        else:
            print(f"❌ {description} - Échec: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def test_import(module_name):
    """Test l'import d'un module"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} disponible")
        return True
    except ImportError:
        print(f"❌ {module_name} non disponible")
        return False

def main():
    print("=" * 60)
    print("🔤 INSTALLATION PADDLEOCR POUR SYMPLISSIME OCR")
    print("=" * 60)

    # Test environnement Python
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Executable: {sys.executable}")

    # Liste des méthodes d'installation à tester (AVEC PaddlePaddle)
    install_methods = [
        ("pip install --break-system-packages paddlepaddle paddleocr pdf2image", "Installation complète système"),
        ("pip install --user paddlepaddle paddleocr pdf2image", "Installation complète utilisateur"),
        ("python -m pip install --break-system-packages paddlepaddle paddleocr pdf2image", "Module pip système complet"),
        ("python -m pip install --user paddlepaddle paddleocr pdf2image", "Module pip utilisateur complet"),
    ]

    # Test si déjà installé
    print("\n🔍 Vérification installation existante...")
    paddle_ok = test_import("paddle")
    paddleocr_ok = test_import("paddleocr")
    pdf2image_ok = test_import("pdf2image")

    if paddle_ok and paddleocr_ok and pdf2image_ok:
        print("🎉 PaddleOCR déjà installé et fonctionnel !")

        # Test rapide de fonctionnement
        try:
            from paddleocr import PaddleOCR
            print("🧪 Test rapide PaddleOCR...")
            # Ne pas initialiser complètement pour éviter le téléchargement de modèles
            print("✅ PaddleOCR importé avec succès")
            return True
        except Exception as e:
            print(f"⚠️ PaddleOCR installé mais problème: {e}")

    # Tentatives d'installation
    print("\n📦 Tentatives d'installation PaddleOCR...")
    for cmd, description in install_methods:
        print(f"\n🚀 {description}")
        if run_command(cmd, description):
            # Test après installation
            if test_import("paddle") and test_import("paddleocr") and test_import("pdf2image"):
                print("🎉 Installation réussie !")
                return True
        print("⏭️ Tentative suivante...")

    # Si toutes les méthodes échouent
    print("\n❌ Toutes les méthodes d'installation ont échoué")
    print("\n🔧 Solutions manuelles à essayer:")
    print("1. Installer PaddlePaddle d'abord:")
    print("   pip install --break-system-packages paddlepaddle")
    print("   pip install --break-system-packages paddleocr pdf2image")
    print("\n2. Créer un environnement virtuel:")
    print("   python -m venv venv")
    print("   venv\\Scripts\\activate")
    print("   pip install paddlepaddle paddleocr pdf2image")
    print("\n3. Utiliser conda:")
    print("   conda install -c conda-forge paddlepaddle paddleocr")
    print("\n3. Installation depuis source:")
    print("   git clone https://github.com/PaddlePaddle/PaddleOCR.git")

    print("\n⚠️ L'API NE FONCTIONNERA PAS sans PaddlePaddle + PaddleOCR")
    return False

if __name__ == "__main__":
    success = main()

    print("\n" + "=" * 60)
    if success:
        print("✅ INSTALLATION TERMINÉE AVEC SUCCÈS")
        print("🚀 Vous pouvez maintenant lancer: go.bat")
    else:
        print("❌ INSTALLATION ÉCHOUÉE")
        print("⚠️ L'API ne fonctionnera PAS sans PaddlePaddle")
        print("🔧 Essayez: fix_paddle.bat")
        print("📋 Ou consultez les solutions manuelles ci-dessus")

    input("\nAppuyez sur Entrée pour continuer...")