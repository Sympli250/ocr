#!/usr/bin/env python3
"""
Test des paramètres PaddleOCR pour diagnostiquer les problèmes
"""
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

console = Console()

def test_paddleocr_params():
    """Test des paramètres PaddleOCR supportés"""
    try:
        from paddleocr import PaddleOCR
        console.print("[green]✅ Import PaddleOCR réussi[/green]")
    except ImportError as e:
        console.print(f"[red]❌ Import PaddleOCR échoué: {e}[/red]")
        return False

    # Test config minimale
    console.print("\n[blue]🧪 Test config minimale...[/blue]")
    try:
        with console.status("[bold green]Initialisation..."):
            ocr = PaddleOCR(use_angle_cls=True, lang="fr", show_log=False)
        console.print("[green]✅ Config minimale OK[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Config minimale échouée: {e}[/red]")

    # Test encore plus minimal
    console.print("\n[blue]🧪 Test ultra-minimal...[/blue]")
    try:
        with console.status("[bold yellow]Initialisation ultra-minimale..."):
            ocr = PaddleOCR(lang="fr")
        console.print("[green]✅ Config ultra-minimale OK[/green]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Config ultra-minimale échouée: {e}[/red]")
        return False

if __name__ == "__main__":
    # Bannière de diagnostic
    banner = Text()
    banner.append("🔍 DIAGNOSTIC PADDLEOCR\n", style="bold cyan")
    banner.append("Test des configurations supportées", style="italic blue")

    panel = Panel(
        banner,
        border_style="bright_cyan",
        padding=(1, 2)
    )
    console.print(panel)

    success = test_paddleocr_params()

    if success:
        console.print("\n[bold green]🎉 PaddleOCR fonctionne correctement![/bold green]")
    else:
        console.print("\n[bold red]❌ Problème avec PaddleOCR[/bold red]")
        sys.exit(1)