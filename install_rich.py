#!/usr/bin/env python3
"""
Script simple pour installer Rich si nécessaire
"""
import sys
import subprocess

def install_rich():
    """Installe Rich si pas déjà présent"""
    try:
        import rich
        print("✅ Rich déjà installé")
        return True
    except ImportError:
        print("📦 Installation de Rich...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
            print("✅ Rich installé avec succès")
            return True
        except subprocess.CalledProcessError:
            print("❌ Erreur lors de l'installation de Rich")
            return False

if __name__ == "__main__":
    if not install_rich():
        sys.exit(1)
    print("🎨 Rich est prêt pour des messages colorés!")