#!/usr/bin/env python3
"""Colle tout ensemble : contenu → contrôles → HTML autonome dans dist/.

    python build.py            # contrôle puis construit dist/index.html
    python build.py --check    # contrôle seulement
    python build.py --strict   # échoue aussi sur les avertissements
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from deckgen.graph import mermaid
from deckgen.loader import load
from deckgen.render import build_html
from deckgen.validate import validate

ROOT = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="contrôler sans construire")
    ap.add_argument("--strict", action="store_true", help="traiter les avertissements comme des erreurs")
    ap.add_argument("--out", default="dist", help="dossier de sortie (défaut : dist)")
    args = ap.parse_args()

    deck = load(ROOT)
    errors, warnings = validate(deck)
    for w in warnings:
        print(f"avertissement : {w}")
    for e in errors:
        print(f"ERREUR : {e}")
    print(f"{len(deck.cards)} cartes, {len(errors)} erreur(s), {len(warnings)} avertissement(s)")
    if errors or (args.strict and warnings):
        return 1
    if args.check:
        return 0

    out = ROOT / args.out
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(build_html(ROOT, deck), encoding="utf-8")
    (out / "dependances.md").write_text("# Dépendances entre cartes\n\n" + mermaid(deck), encoding="utf-8")
    (out / "cartes.json").write_text(json.dumps([asdict(c) for c in deck.cards], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Écrit : {out / 'index.html'}, dependances.md, cartes.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
