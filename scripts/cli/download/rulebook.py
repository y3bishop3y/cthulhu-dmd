#!/usr/bin/env python3
"""
Download the Death May Die rulebook PDF.
"""

import sys
from pathlib import Path
from typing import Final

try:
    import click
    import requests
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run ./scripts/download_rulebook.py [options]\n"
        "  2. source .venv/bin/activate && ./scripts/download_rulebook.py [options]\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
RULEBOOK_URL: Final[str] = "https://resources.cmon.com/DMD_Rulebook_web.pdf"
RULEBOOK_FILENAME: Final[str] = "DMD_Rulebook_web.pdf"
HTTP_TIMEOUT_SECONDS: Final[int] = 60


def download_rulebook(output_path: Path) -> bool:
    """Download the rulebook PDF."""
    try:
        console.print(f"[cyan]Downloading rulebook from {RULEBOOK_URL}...[/cyan]")
        response = requests.get(RULEBOOK_URL, timeout=HTTP_TIMEOUT_SECONDS, stream=True)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading", total=total_size if total_size > 0 else None)

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress.update(task, advance=len(chunk))

        console.print(
            f"[green]✓ Downloaded {downloaded / 1024 / 1024:.2f} MB to {output_path}[/green]"
        )
        return True

    except Exception as e:
        console.print(f"[red]Error downloading rulebook:[/red] {e}")
        return False


@click.command()
@click.option(
    "--data-dir",
    default="data",
    type=click.Path(path_type=Path),
    help="Data directory to save the rulebook",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing file if it exists",
)
def main(data_dir: Path, force: bool):
    """Download the Death May Die rulebook PDF."""

    console.print(
        Panel.fit(
            f"[bold cyan]Death May Die Rulebook Downloader[/bold cyan]\nSource: {RULEBOOK_URL}",
            border_style="cyan",
        )
    )

    output_path = data_dir / RULEBOOK_FILENAME

    if output_path.exists() and not force:
        console.print(f"[yellow]Rulebook already exists at {output_path}[/yellow]")
        console.print("Use --force to overwrite")
        return

    if download_rulebook(output_path):
        console.print("\n[green]✓ Download complete![/green]")
    else:
        console.print("\n[red]✗ Download failed[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
