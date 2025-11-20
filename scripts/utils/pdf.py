#!/usr/bin/env python3
"""
Shared PDF parsing utilities.

This module provides common PDF parsing functions used across scripts.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pdfplumber
except ImportError as e:
    print(
        f"Error: Missing required dependency: {e.name}\n\nInstall with: pip install pdfplumber\n",
        file=sys.stderr,
    )
    raise


def extract_text_from_pdf(
    pdf_path: Path,
    page_numbers: Optional[List[int]] = None,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
) -> str:
    """Extract text from PDF file.

    Args:
        pdf_path: Path to PDF file
        page_numbers: Specific page numbers to extract (0-indexed)
        start_page: Start page number (0-indexed, inclusive)
        end_page: End page number (0-indexed, exclusive)

    Returns:
        Extracted text as string

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If page numbers are invalid
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    text_parts: List[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        if page_numbers is not None:
            # Extract specific pages
            for page_num in page_numbers:
                if page_num < 0 or page_num >= total_pages:
                    raise ValueError(f"Page number {page_num} out of range (0-{total_pages - 1})")
                text = pdf.pages[page_num].extract_text() or ""
                text_parts.append(text)
        elif start_page is not None or end_page is not None:
            # Extract page range
            start = start_page if start_page is not None else 0
            end = end_page if end_page is not None else total_pages

            if start < 0 or end > total_pages or start >= end:
                raise ValueError(f"Invalid page range: {start}-{end} (total pages: {total_pages})")

            for page_num in range(start, end):
                text = pdf.pages[page_num].extract_text() or ""
                text_parts.append(text)
        else:
            # Extract all pages
            for page in pdf.pages:
                text = page.extract_text() or ""
                text_parts.append(text)

    return "\n".join(text_parts)


def extract_tables_from_pdf(
    pdf_path: Path,
    page_numbers: Optional[List[int]] = None,
) -> List[List[List[str]]]:
    """Extract tables from PDF file.

    Args:
        pdf_path: Path to PDF file
        page_numbers: Specific page numbers to extract (0-indexed)

    Returns:
        List of tables, where each table is a list of rows,
        and each row is a list of cell strings
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    all_tables: List[List[List[str]]] = []

    with pdfplumber.open(pdf_path) as pdf:
        if page_numbers is not None:
            pages_to_process = page_numbers
        else:
            pages_to_process = list(range(len(pdf.pages)))

        for page_num in pages_to_process:
            if page_num < 0 or page_num >= len(pdf.pages):
                continue

            page = pdf.pages[page_num]
            tables = page.extract_tables()

            if tables:
                all_tables.extend(tables)

    return all_tables


def extract_text_from_pdf_pages(
    pdf_path: Path,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    console: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Extract text from PDF pages with page information.

    Args:
        pdf_path: Path to PDF file
        start_page: Optional starting page number (1-indexed)
        end_page: Optional ending page number (1-indexed, inclusive)
        console: Optional Rich console for progress display

    Returns:
        List of dicts with 'page' and 'text' keys
    """
    pages_data: List[Dict[str, Any]] = []

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            start_idx = (start_page - 1) if start_page else 0
            end_idx = end_page if end_page else total_pages

            # Show progress if console provided
            if console:
                from rich.progress import (
                    BarColumn,
                    Progress,
                    SpinnerColumn,
                    TaskProgressColumn,
                    TextColumn,
                )

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task("Extracting text from PDF", total=end_idx - start_idx)
                    for page_num in range(start_idx, min(end_idx, total_pages)):
                        page = pdf.pages[page_num]
                        text = page.extract_text()
                        if text:
                            pages_data.append({"page": page_num + 1, "text": text})
                        progress.update(task, advance=1)
            else:
                for page_num in range(start_idx, min(end_idx, total_pages)):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    if text:
                        pages_data.append({"page": page_num + 1, "text": text})

        return pages_data

    except Exception as e:
        error_msg = f"Error extracting text from PDF: {e}"
        if console:
            console.print(f"[red]{error_msg}[/red]")
        else:
            print(error_msg, file=sys.stderr)
        return []


def get_pdf_page_count(pdf_path: Path) -> int:
    """Get the number of pages in a PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Number of pages
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        return len(pdf.pages)
