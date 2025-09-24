#!/usr/bin/env python3
"""
Script de vérification et mise à jour de compatibilité PaddleOCR
Détecte la version et ajuste automatiquement la configuration
"""
import sys
import json

def check_paddleocr_compatibility():
    """Vérifie les paramètres supportés par la version PaddleOCR installée"""
    try:
        import paddleocr
        from paddleocr import PaddleOCR

        version = getattr(paddleocr, '__version__', 'unknown')
        print(f"🔍 Version PaddleOCR détectée: {version}")

        # Test des paramètres supportés
        supported_params = {}

        # Test show_log (supprimé en v3.2.0+)
        try:
            test = PaddleOCR(lang="fr", show_log=False)
            supported_params['show_log'] = True
            print("✅ Paramètre 'show_log' supporté")
        except Exception:
            supported_params['show_log'] = False
            print("❌ Paramètre 'show_log' NON supporté (version récente)")

        # Test use_angle_cls
        try:
            test = PaddleOCR(lang="fr", use_angle_cls=True)
            supported_params['use_angle_cls'] = True
            print("✅ Paramètre 'use_angle_cls' supporté")
        except Exception:
            supported_params['use_angle_cls'] = False
            print("❌ Paramètre 'use_angle_cls' NON supporté")

        # Test det_db_thresh
        try:
            test = PaddleOCR(lang="fr", det_db_thresh=0.3)
            supported_params['det_db_thresh'] = True
            print("✅ Paramètre 'det_db_thresh' supporté")
        except Exception:
            supported_params['det_db_thresh'] = False
            print("❌ Paramètre 'det_db_thresh' NON supporté")

        # Test de base
        try:
            test = PaddleOCR(lang="fr")
            print("✅ Configuration minimale fonctionnelle")
            basic_works = True
        except Exception as e:
            print(f"❌ Configuration minimale échoue: {e}")
            basic_works = False

        return {
            'version': version,
            'basic_works': basic_works,
            'supported_params': supported_params,
            'recommended_config': generate_config(supported_params)
        }

    except ImportError:
        print("❌ PaddleOCR non installé")
        return None
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return None

def generate_config(supported_params):
    """Génère une configuration optimale selon les paramètres supportés"""
    configs = {}

    # Configuration de base pour tous les profils
    base_config = {"lang": "fr"}

    # Ajouter les paramètres supportés
    if supported_params.get('use_angle_cls', False):
        base_config['use_angle_cls'] = True
    if supported_params.get('show_log', False):
        base_config['show_log'] = False

    # Configuration par profil
    configs['printed'] = base_config.copy()
    configs['english'] = {**base_config, 'lang': 'en'}
    configs['multilang'] = base_config.copy()

    if supported_params.get('det_db_thresh', False):
        configs['handwriting'] = {**base_config, 'det_db_thresh': 0.2}
        configs['legal'] = {**base_config, 'det_db_thresh': 0.3}
    else:
        configs['handwriting'] = base_config.copy()
        configs['legal'] = base_config.copy()

    if supported_params.get('det_db_box_thresh', False):
        configs['scanned'] = {**base_config, 'det_db_box_thresh': 0.5}
    else:
        configs['scanned'] = base_config.copy()

    return configs

def main():
    print("=" * 60)
    print("🔤 VÉRIFICATION COMPATIBILITÉ PADDLEOCR")
    print("=" * 60)

    result = check_paddleocr_compatibility()

    if result is None:
        print("\n❌ Impossible de tester PaddleOCR")
        sys.exit(1)

    print(f"\n📊 RÉSUMÉ COMPATIBILITÉ")
    print(f"Version: {result['version']}")
    print(f"Configuration de base: {'✅ OK' if result['basic_works'] else '❌ Échec'}")

    print(f"\n🔧 PARAMÈTRES SUPPORTÉS:")
    for param, supported in result['supported_params'].items():
        status = "✅ Oui" if supported else "❌ Non"
        print(f"  {param}: {status}")

    print(f"\n⚙️ CONFIGURATION RECOMMANDÉE:")
    config = result['recommended_config']
    print(json.dumps(config, indent=2, ensure_ascii=False))

    print(f"\n💡 CONSEIL:")
    if not result['supported_params'].get('show_log', True):
        print("  - Retirez 'show_log' de vos configurations (version récente)")
    if result['basic_works']:
        print("  - PaddleOCR fonctionne correctement avec cette configuration")
    else:
        print("  - Problème avec PaddleOCR, mode simulation recommandé")

if __name__ == "__main__":
    main()