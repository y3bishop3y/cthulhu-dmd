#!/usr/bin/env python3
"""
Reorganize data directory structure according to Phase 1 plan.

This script:
1. Moves season1/characters/* to season1/* (flatten structure)
2. Moves character-book.pdf from season1/characters/ to season1/
3. Archives *_annotated.png files to .archive/annotated/
4. Archives *_ocr_preprocessed.png files to .archive/ocr_preprocessed/
"""

import shutil
import sys
from pathlib import Path

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARCHIVE_DIR = DATA_DIR / ".archive"


def main():
    """Main reorganization function."""
    print("=" * 60)
    print("Data Directory Reorganization")
    print(f"Data directory: {DATA_DIR}")
    print("=" * 60)
    
    # Step 1: Move season1/characters/* to season1/*
    print("\n[Step 1] Flattening season1 structure...")
    season1_dir = DATA_DIR / "season1"
    characters_dir = season1_dir / "characters"
    
    if characters_dir.exists():
        items = list(characters_dir.iterdir())
        print(f"  Found {len(items)} items in season1/characters/")
        
        for item in items:
            if item.is_dir():
                # Move character directory
                dest = season1_dir / item.name
                if dest.exists():
                    print(f"  ⚠ Warning: {dest} already exists. Skipping {item.name}")
                else:
                    print(f"  → Moving {item.name}/ to season1/")
                    shutil.move(str(item), str(dest))
            elif item.name == "character-book.pdf":
                # Move PDF to season1 root
                dest = season1_dir / item.name
                if dest.exists():
                    print(f"  ⚠ Warning: {dest} already exists. Skipping")
                else:
                    print(f"  → Moving character-book.pdf to season1/")
                    shutil.move(str(item), str(dest))
            else:
                print(f"  ⚠ Skipping unexpected file: {item.name}")
        
        # Remove empty characters directory
        try:
            characters_dir.rmdir()
            print("  ✓ Removed empty characters/ directory")
        except OSError:
            print("  ⚠ Warning: characters/ directory not empty or cannot be removed")
        
        print("  ✓ Season1 structure flattened")
    else:
        print("  ⚠ season1/characters/ directory not found. Skipping.")
    
    # Step 2: Archive annotated files
    print("\n[Step 2] Archiving *_annotated.png files...")
    annotated_files = list(DATA_DIR.rglob("*_annotated.png"))
    if annotated_files:
        archive_subdir = ARCHIVE_DIR / "annotated"
        archive_subdir.mkdir(parents=True, exist_ok=True)
        print(f"  Found {len(annotated_files)} files to archive")
        
        for file_path in annotated_files:
            # Preserve relative path structure in archive
            rel_path = file_path.relative_to(DATA_DIR)
            dest = archive_subdir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), str(dest))
        
        print(f"  ✓ Archived {len(annotated_files)} files to {archive_subdir}")
    else:
        print("  No *_annotated.png files found")
    
    # Step 3: Archive OCR preprocessed files
    print("\n[Step 3] Archiving *_ocr_preprocessed.png files...")
    ocr_files = list(DATA_DIR.rglob("*_ocr_preprocessed.png"))
    if ocr_files:
        archive_subdir = ARCHIVE_DIR / "ocr_preprocessed"
        archive_subdir.mkdir(parents=True, exist_ok=True)
        print(f"  Found {len(ocr_files)} files to archive")
        
        for file_path in ocr_files:
            # Preserve relative path structure in archive
            rel_path = file_path.relative_to(DATA_DIR)
            dest = archive_subdir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), str(dest))
        
        print(f"  ✓ Archived {len(ocr_files)} files to {archive_subdir}")
    else:
        print("  No *_ocr_preprocessed.png files found")
    
    # Step 4: Verify structure
    print("\n[Step 4] Verifying directory structure...")
    seasons = [
        "season1", "season2", "season3", "season4",
        "comic-book-extras", "comic-book-v2", "extra-promos",
        "unknowable-box", "unspeakable-box"
    ]
    
    issues = []
    for season_name in seasons:
        season_dir = DATA_DIR / season_name
        if not season_dir.exists():
            continue
        
        # Check for nested characters/ directory (shouldn't exist after reorganization)
        characters_subdir = season_dir / "characters"
        if characters_subdir.exists():
            issues.append(f"{season_name}: Still has characters/ subdirectory")
    
    if issues:
        print("  ⚠ Found structure issues:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✓ Directory structure is consistent")
    
    print("\n" + "=" * 60)
    print("✓ Reorganization complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

