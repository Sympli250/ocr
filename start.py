#!/usr/bin/env python3
"""
Script de démarrage pour Symplissime OCR API
Réalisé par Ayi NEDJIMI Consultants
"""
import os
import sys
import subprocess
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.align import Align

console = Console()

def show_banner():
    """Affiche la bannière colorée"""
    banner_text = Text()
    banner_text.append("🔤 SYMPLISSIME OCR\n", style="bold magenta")
    banner_text.append("    Version 1.1.0\n", style="bold cyan")
    banner_text.append("Réalisé par Ayi NEDJIMI Consultants", style="italic blue")

    panel = Panel(
        Align.center(banner_text),
        border_style="bright_magenta",
        padding=(1, 2)
    )
    console.print(panel)

def check_dependencies():
    """Vérifie les dépendances système"""
    console.print("\n[bold yellow]📦 Vérification des dépendances...[/bold yellow]")

    deps = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("paddleocr", "PaddleOCR"),
        ("pdf2image", "PDF2Image"),
        ("PIL", "Pillow")
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Dépendance", style="cyan")
    table.add_column("Statut", justify="center")

    all_good = True

    for module, name in deps:
        try:
            __import__(module)
            table.add_row(name, "[green]✅ OK[/green]")
        except ImportError:
            table.add_row(name, "[red]❌ Manquant[/red]")
            all_good = False

    console.print(table)

    if not all_good:
        console.print("[red]❌ Dépendances manquantes détectées[/red]")
        console.print("[yellow]💡 Installation automatique en cours...[/yellow]")
        return False

    # Test spécifique PaddleOCR
    console.print("\n[bold blue]🔍 Test PaddleOCR...[/bold blue]")
    try:
        from paddleocr import PaddleOCR
        with console.status("[bold green]Initialisation PaddleOCR..."):
            ocr = PaddleOCR(lang="fr", show_log=False)
        console.print("[green]✅ PaddleOCR fonctionne correctement[/green]")
        return True
    except Exception as ocr_error:
        console.print(f"[yellow]⚠️ PaddleOCR disponible mais erreur: {ocr_error}[/yellow]")
        console.print("[blue]🔧 L'API utilisera un fallback automatique[/blue]")
        return True

def install_dependencies():
    """Installe les dépendances"""
    console.print("\n[bold yellow]📦 Installation des dépendances...[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Installation en cours...", total=1)

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                progress.update(task, completed=1)
                console.print("[green]✅ Dépendances installées avec succès[/green]")
                return True
            else:
                console.print("[red]❌ Erreur lors de l'installation[/red]")
                console.print(f"[red]Détails: {result.stderr}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Exception: {e}[/red]")
            return False

def start_server():
    """Démarre le serveur"""
    console.print("\n[bold green]🚀 Démarrage du serveur OCR...[/bold green]")

    # Configuration par défaut
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    log_level = os.getenv("LOG_LEVEL", "info")

    # Tableau d'information
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Label", style="bold cyan")
    info_table.add_column("Value", style="bright_white")

    info_table.add_row("🌐 Serveur:", f"http://{host}:{port}")
    info_table.add_row("📝 Documentation:", f"http://localhost:{port}/docs")
    info_table.add_row("❤️ Health Check:", f"http://localhost:{port}/health")
    info_table.add_row("🧪 Test Interface:", "http://localhost/testocr.php")

    panel = Panel(
        info_table,
        title="[bold green]🔗 Accès API[/bold green]",
        border_style="green",
        padding=(1, 1)
    )
    console.print(panel)

    try:
        import uvicorn
        from app import app

        console.print("[bold magenta]Appuyez sur Ctrl+C pour arrêter[/bold magenta]\n")

        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            reload=False
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Arrêt du serveur...[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Erreur de démarrage: {e}[/red]")
        return False

    return True

if __name__ == "__main__":
    # Bannière colorée
    show_banner()

    # Vérification des dépendances
    if not check_dependencies():
        console.print("\n[yellow]🔧 Installation automatique des dépendances...[/yellow]")
        if not install_dependencies():
            console.print("\n[red]💥 Échec de l'installation - Arrêt[/red]")
            sys.exit(1)

        # Re-vérification après installation
        console.print("\n[blue]🔄 Re-vérification après installation...[/blue]")
        if not check_dependencies():
            console.print("\n[red]💥 Problème persistant - Arrêt[/red]")
            sys.exit(1)

    # Démarrage du serveur
    if not start_server():
        console.print("\n[red]💥 Erreur de démarrage - Arrêt[/red]")
        sys.exit(1)