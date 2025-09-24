#!/usr/bin/env python3
"""
Script de test pour Symplissime OCR API
Réalisé par Ayi NEDJIMI Consultants
"""
import requests
import json
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich import print as rprint

console = Console()

API_BASE_URL = "http://localhost:8000"

def create_test_image():
    """Crée une image de test avec du texte"""
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)

    # Texte de test
    text = "Test OCR\nSymplissime API\n2024"

    try:
        # Essaie d'utiliser une police par défaut
        font = ImageFont.load_default()
    except:
        font = None

    # Position du texte
    x, y = 50, 50
    draw.text((x, y), text, fill='black', font=font)

    # Sauvegarde en bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    return img_bytes.getvalue()

def test_health_check():
    """Test du health check"""
    console.print("[bold blue]🏥 Test Health Check...[/bold blue]")
    try:
        with console.status("[bold green]Vérification du serveur..."):
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            console.print(f"[green]✅ Health Check OK[/green]")
            console.print(f"[dim]Version: {data.get('version', 'N/A')}[/dim]")
            return True
        else:
            console.print(f"[red]❌ Health Check Failed: {response.status_code}[/red]")
            return False
    except Exception as e:
        console.print(f"[red]❌ Erreur Health Check: {e}[/red]")
        return False

def test_ocr_endpoint():
    """Test de l'endpoint OCR principal"""
    console.print("[bold magenta]🔤 Test Endpoint OCR...[/bold magenta]")

    # Création d'une image de test
    test_image = create_test_image()
    files = {'file': ('test.png', test_image, 'image/png')}

    # Test avec différents profils
    profiles = ['printed', 'english', 'legal']
    formats = ['json', 'text', 'html']
    total_tests = len(profiles) * len(formats)

    results = []

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        console=console
    ) as progress:

        task = progress.add_task("Tests OCR...", total=total_tests)
        current_test = 0

        for profile in profiles:
            for output_format in formats:
                current_test += 1
                test_desc = f"Test {profile} -> {output_format} ({current_test}/{total_tests})"
                progress.update(task, description=test_desc)

                params = {
                    'profile': profile,
                    'output_format': output_format,
                    'enhance': 'contrast'
                }

                try:
                    start_time = time.time()
                    response = requests.post(
                        f"{API_BASE_URL}/ocr",
                        files=files,
                        params=params,
                        timeout=30
                    )
                    processing_time = time.time() - start_time

                    if response.status_code == 200:
                        results.append({
                            'profile': profile,
                            'format': output_format,
                            'status': 'success',
                            'time': processing_time
                        })

                        # Afficher un échantillon pour JSON
                        if output_format == 'json':
                            try:
                                data = response.json()
                                total_lines = data.get('metadata', {}).get('total_lines', 0)
                                console.print(f"  [green]✅ {profile}/{output_format} - {total_lines} lignes ({processing_time:.2f}s)[/green]")
                            except:
                                console.print(f"  [green]✅ {profile}/{output_format} ({processing_time:.2f}s)[/green]")
                        else:
                            console.print(f"  [green]✅ {profile}/{output_format} ({processing_time:.2f}s)[/green]")
                    else:
                        console.print(f"  [red]❌ {profile}/{output_format} - Erreur {response.status_code}[/red]")
                        results.append({
                            'profile': profile,
                            'format': output_format,
                            'status': 'error',
                            'error': response.status_code
                        })

                except Exception as e:
                    console.print(f"  [red]❌ {profile}/{output_format} - Exception: {e}[/red]")
                    results.append({
                        'profile': profile,
                        'format': output_format,
                        'status': 'exception',
                        'error': str(e)
                    })

                progress.advance(task)

    return results

def test_error_handling():
    """Test de la gestion d'erreurs"""
    console.print("[bold yellow]⚠️ Test Gestion d'erreurs...[/bold yellow]")

    error_tests = Table(show_header=True, header_style="bold magenta")
    error_tests.add_column("Test", style="cyan")
    error_tests.add_column("Résultat", justify="center")
    error_tests.add_column("Détails", style="dim")

    # Test fichier vide
    console.print("  [blue]📄 Test fichier vide...[/blue]")
    files = {'file': ('empty.txt', b'', 'text/plain')}
    response = requests.post(f"{API_BASE_URL}/ocr", files=files)
    if response.status_code == 400:
        error_tests.add_row("Fichier vide", "[green]✅ OK[/green]", "Correctement rejeté")
    else:
        error_tests.add_row("Fichier vide", "[red]❌ ÉCHEC[/red]", f"Code: {response.status_code}")

    # Test profil invalide
    console.print("  [blue]🎯 Test profil invalide...[/blue]")
    test_image = create_test_image()
    files = {'file': ('test.png', test_image, 'image/png')}
    params = {'profile': 'invalid_profile'}
    response = requests.post(f"{API_BASE_URL}/ocr", files=files, params=params)
    if response.status_code == 422:
        error_tests.add_row("Profil invalide", "[green]✅ OK[/green]", "Validation réussie")
    else:
        error_tests.add_row("Profil invalide", "[red]❌ ÉCHEC[/red]", f"Code: {response.status_code}")

    console.print(error_tests)

def print_summary(results):
    """Affiche un résumé des tests"""
    total = len(results)
    success = sum(1 for r in results if r['status'] == 'success')
    success_rate = (success/total*100) if total > 0 else 0

    # Tableau de résumé
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Métrique", style="cyan")
    summary_table.add_column("Valeur", justify="center")

    summary_table.add_row("Total des tests", str(total))
    summary_table.add_row("Succès", f"[green]{success}[/green]")
    summary_table.add_row("Échecs", f"[red]{total - success}[/red]")

    if success_rate >= 80:
        rate_color = "green"
    elif success_rate >= 60:
        rate_color = "yellow"
    else:
        rate_color = "red"
    summary_table.add_row("Taux de réussite", f"[{rate_color}]{success_rate:.1f}%[/{rate_color}]")

    if success > 0:
        avg_time = sum(r.get('time', 0) for r in results if r['status'] == 'success') / success
        summary_table.add_row("Temps moyen", f"{avg_time:.2f}s")

    panel = Panel(
        summary_table,
        title="[bold cyan]📊 Résumé des Tests[/bold cyan]",
        border_style="cyan"
    )
    console.print(panel)

    # Détail des échecs
    errors = [r for r in results if r['status'] != 'success']
    if errors:
        console.print("\n[red]❌ Échecs détaillés:[/red]")
        for error in errors:
            console.print(f"  [red]•[/red] {error['profile']}/{error['format']}: {error.get('error', 'Unknown')}")

def main():
    """Fonction principale"""
    # Bannière de tests
    banner = Text()
    banner.append("🔤 TESTS SYMPLISSIME OCR API\n", style="bold magenta")
    banner.append(f"URL: {API_BASE_URL}", style="italic blue")

    panel = Panel(
        banner,
        border_style="bright_magenta",
        padding=(1, 2)
    )
    console.print(panel)

    # Test de base
    if not test_health_check():
        console.print("[red]❌ Le serveur ne répond pas. Vérifiez qu'il est démarré.[/red]")
        sys.exit(1)

    console.print()

    # Tests principaux
    results = test_ocr_endpoint()

    console.print()

    # Tests d'erreurs
    test_error_handling()

    console.print()

    # Résumé
    print_summary(results)

    console.print(f"\n[bold green]🏁 Tests terminés![/bold green]")

if __name__ == "__main__":
    main()