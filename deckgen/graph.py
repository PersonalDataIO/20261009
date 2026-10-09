"""Graphe des dépendances au format Mermaid (à ouvrir avec l'aperçu Markdown de VS Code)."""
from __future__ import annotations

from .loader import Deck


def display_id(card_id: str) -> str:
    if card_id.endswith("Qc"):
        return card_id[:-2] + "cQm"
    if card_id.endswith("Qm"):
        return card_id[:-2] + "mQc"
    return card_id


def mermaid(deck: Deck) -> str:
    lines = ["```mermaid", "flowchart LR"]
    for s in deck.sections:
        if s.numero is None:
            continue
        lines.append(f'  subgraph F{s.key}["{s.key}. {s.theme}"]')
        for c in deck.section_cards(s.key):
            lines.append(f'    n{c.id}["{display_id(c.id)}"]')
        lines.append("  end")
    for c in deck.cards:
        if c.section in ("P", "J") and c.serrure:
            lines.append(f'  n{c.id}(("{display_id(c.id)}"))')
    for c in deck.cards:
        for k in c.serrure:
            lines.append(f'  n{k} -->|{display_id(k)}| n{c.id}')
    lines.append("```")
    return "\n".join(lines) + "\n"
