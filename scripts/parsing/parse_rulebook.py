#!/usr/bin/env python3
"""
Parse the Death May Die rulebook PDF into structured markdown.
Extracts sections, subsections, and content for easy reference.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, Final, List, Optional

try:
    import click
    from pydantic import BaseModel, Field
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

    from scripts.utils.pdf import extract_text_from_pdf_pages
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\n"
        "To run this script, use one of:\n"
        "  1. uv run python scripts/parsing/parse_rulebook.py [options]\n"
        "  2. source .venv/bin/activate && python scripts/parsing/parse_rulebook.py [options]\n",
        file=sys.stderr,
    )
    sys.exit(1)

console = Console()

# Constants
RULEBOOK_FILENAME: Final[str] = "DMD_Rulebook_web.pdf"
OUTPUT_MARKDOWN: Final[str] = "rulebook.md"
OUTPUT_TEXT: Final[str] = "rulebook.txt"

# Section patterns
SECTION_PATTERN: Final[str] = r"^[A-Z][A-Z\s]+$"  # All caps section headers
SUBSECTION_PATTERN: Final[str] = r"^[A-Z][a-z\s]+"  # Title case subsections
PAGE_NUMBER_PATTERN: Final[str] = r"^\d+$"  # Page numbers


# Pydantic Models
class RulebookSection(BaseModel):
    """Represents a section of the rulebook."""

    title: str
    level: int = Field(description="Section level (1=main, 2=subsection, etc.)")
    content: str = ""
    subsections: List["RulebookSection"] = Field(default_factory=list)
    page_number: Optional[int] = None


class Rulebook(BaseModel):
    """Complete parsed rulebook."""

    title: str = "Death May Die Rulebook"
    sections: List[RulebookSection] = Field(default_factory=list)
    total_pages: int = 0


def is_section_header(text: str) -> bool:
    """Check if text looks like a section header."""
    text_clean = text.strip()
    if not text_clean:
        return False

    # All caps and reasonable length
    if text_clean.isupper() and 3 < len(text_clean) < 100:
        return True

    # Title case with multiple words
    if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$", text_clean):
        return True

    return False


# PDF extraction now uses utils/pdf.py
# extract_text_from_pdf() returns List[Dict[str, Any]] with 'page' and 'text' keys


def parse_rulebook_structure(pages_data: List[Dict[str, Any]]) -> Rulebook:
    """Parse PDF pages into structured sections."""
    rulebook = Rulebook(total_pages=len(pages_data))

    current_section: Optional[RulebookSection] = None
    current_subsection: Optional[RulebookSection] = None
    content_buffer: List[str] = []

    for page_data in pages_data:
        page_num = page_data["page"]
        text = page_data["text"]
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip page numbers
            if re.match(PAGE_NUMBER_PATTERN, line):
                continue

            # Check if this is a main section (all caps, short)
            if line.isupper() and 3 < len(line) < 80 and not line.endswith("."):
                # Save previous section if exists
                if current_section:
                    if content_buffer:
                        if current_subsection:
                            current_subsection.content = "\n".join(content_buffer)
                            current_section.subsections.append(current_subsection)
                            current_subsection = None
                        else:
                            current_section.content = "\n".join(content_buffer)
                    rulebook.sections.append(current_section)

                # Start new section
                current_section = RulebookSection(title=line.title(), level=1, page_number=page_num)
                content_buffer = []
                current_subsection = None

            # Check if this is a subsection (title case, might be numbered)
            elif (
                current_section
                and re.match(r"^[A-Z][a-z]+", line)
                and len(line) < 100
                and not line.endswith(".")
            ):
                # Save previous subsection if exists
                if current_subsection:
                    current_subsection.content = "\n".join(content_buffer)
                    current_section.subsections.append(current_subsection)
                    content_buffer = []

                # Start new subsection
                current_subsection = RulebookSection(title=line, level=2, page_number=page_num)

            # Regular content
            else:
                content_buffer.append(line)

        # Add page break marker
        content_buffer.append(f"\n--- Page {page_num} ---\n")

    # Don't forget the last section
    if current_section:
        if content_buffer:
            if current_subsection:
                current_subsection.content = "\n".join(content_buffer)
                current_section.subsections.append(current_subsection)
            else:
                current_section.content = "\n".join(content_buffer)
        rulebook.sections.append(current_section)

    return rulebook


def rulebook_to_markdown(rulebook: Rulebook) -> str:
    """Convert rulebook to markdown format."""
    md_lines: List[str] = []

    md_lines.append(f"# {rulebook.title}\n")
    md_lines.append(f"*Total Pages: {rulebook.total_pages}*\n\n")
    md_lines.append("---\n\n")

    for section in rulebook.sections:
        # Main section
        md_lines.append(f"## {section.title}\n")
        if section.page_number:
            md_lines.append(f"*Page {section.page_number}*\n\n")

        # Section content
        if section.content:
            md_lines.append(f"{section.content}\n\n")

        # Subsections
        for subsection in section.subsections:
            md_lines.append(f"### {subsection.title}\n")
            if subsection.page_number:
                md_lines.append(f"*Page {subsection.page_number}*\n\n")
            if subsection.content:
                md_lines.append(f"{subsection.content}\n\n")

        md_lines.append("---\n\n")

    return "".join(md_lines)


def rulebook_to_text(rulebook: Rulebook) -> str:
    """Convert rulebook to plain text format."""
    text_lines: List[str] = []

    text_lines.append(f"{rulebook.title}\n")
    text_lines.append(f"Total Pages: {rulebook.total_pages}\n\n")
    text_lines.append("=" * 80 + "\n\n")

    for section in rulebook.sections:
        # Main section
        text_lines.append(f"{section.title}\n")
        text_lines.append("=" * 80 + "\n")
        if section.page_number:
            text_lines.append(f"Page {section.page_number}\n\n")

        # Section content
        if section.content:
            text_lines.append(f"{section.content}\n\n")

        # Subsections
        for subsection in section.subsections:
            text_lines.append(f"{subsection.title}\n")
            text_lines.append("-" * 80 + "\n")
            if subsection.page_number:
                text_lines.append(f"Page {subsection.page_number}\n\n")
            if subsection.content:
                text_lines.append(f"{subsection.content}\n\n")

        text_lines.append("=" * 80 + "\n\n")

    return "".join(text_lines)


@click.command()
@click.option(
    "--pdf-path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to the rulebook PDF file",
)
@click.option(
    "--data-dir",
    default="data",
    type=click.Path(path_type=Path),
    help="Data directory containing the rulebook PDF",
)
@click.option(
    "--output-format",
    type=click.Choice(["markdown", "text", "both"], case_sensitive=False),
    default="markdown",
    help="Output format",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    help="Output directory (defaults to same as PDF)",
)
def main(
    pdf_path: Optional[Path],
    data_dir: Path,
    output_format: str,
    output_dir: Optional[Path],
):
    """Parse the Death May Die rulebook PDF into structured text/markdown."""

    console.print(
        Panel.fit(
            "[bold cyan]Death May Die Rulebook Parser[/bold cyan]\n"
            "Extracts structured content from PDF",
            border_style="cyan",
        )
    )

    # Determine PDF path
    if pdf_path:
        pdf_file = pdf_path
    else:
        pdf_file = data_dir / RULEBOOK_FILENAME

    if not pdf_file.exists():
        console.print(f"[red]PDF not found at {pdf_file}[/red]")
        console.print("Run './scripts/download_rulebook.py' first to download it")
        sys.exit(1)

    # Determine output directory
    if output_dir:
        out_dir = output_dir
    else:
        out_dir = pdf_file.parent

    console.print(f"\n[cyan]Parsing PDF: {pdf_file}[/cyan]")

    # Extract text from PDF
    console.print("\n[cyan]Extracting text from PDF...[/cyan]")
    pages_data = extract_text_from_pdf_pages(pdf_file, console=console)

    if not pages_data:
        console.print("[red]Failed to extract text from PDF[/red]")
        sys.exit(1)

    console.print(f"[green]Extracted text from {len(pages_data)} pages[/green]")

    # Parse structure
    console.print("\n[cyan]Parsing structure...[/cyan]")
    rulebook = parse_rulebook_structure(pages_data)

    console.print(f"[green]Found {len(rulebook.sections)} main sections[/green]")

    # Generate output
    if output_format in ("markdown", "both"):
        md_content = rulebook_to_markdown(rulebook)
        md_path = out_dir / OUTPUT_MARKDOWN
        md_path.write_text(md_content, encoding="utf-8")
        console.print(f"[green]✓ Saved markdown to {md_path}[/green]")

    if output_format in ("text", "both"):
        text_content = rulebook_to_text(rulebook)
        text_path = out_dir / OUTPUT_TEXT
        text_path.write_text(text_content, encoding="utf-8")
        console.print(f"[green]✓ Saved text to {text_path}[/green]")

    console.print("\n[green]✓ Parsing complete![/green]")


if __name__ == "__main__":
    main()
