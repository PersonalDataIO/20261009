"""Lecture du contenu (Markdown + front matter YAML) et construction du modèle du jeu."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
import re


def read_md(path: Path) -> tuple[dict[str, Any], str]:
    """Retourne (front matter, corps) d'un fichier Markdown."""
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        return {}, raw.strip()
    _, fm, body = raw.split("---", 2)
    return yaml.safe_load(fm) or {}, body.strip()

def localized_fields(data: dict[str, Any], language: str) -> dict[str, Any]:
    """Overlay a locale's translations on the source-language fields."""
    fields = {key: value for key, value in data.items() if key != "translations"}
    fields.update((data.get("translations") or {}).get(language, {}))
    return fields


def merge_config(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge translated config while replacing localized lists."""
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


def read_family_cards(path: Path, body: str, number: int, types: dict[str, dict[str, Any]], ordre: list[str], language: str) -> list[Card]:
    """Read card sections embedded in a family's single Markdown file."""
    headings = list(re.finditer(r"(?m)^## Carte ([A-Za-z0-9-]+)\s*$", body))
    if not headings:
        return []

    cards = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        block = body[heading.end():end].strip()
        match = re.match(r"\A```ya?ml\s*\n(.*?)\n```\s*\n?(.*)\Z", block, re.DOTALL)
        if not match:
            raise ValueError(f"{path}: la carte {heading.group(1)} doit commencer par un bloc YAML")
        metadata = localized_fields(yaml.safe_load(match.group(1)) or {}, language)
        card_type = metadata["type"]
        serrure = metadata.get("serrure")
        if serrure is None:
            serrure = [f"{number}{item}" for item in types[card_type].get("serrure", [])]
        cards.append(Card(
            id=heading.group(1), type=card_type, section=str(number), titre=metadata["titre"],
            texte=metadata.get("text", match.group(2).strip()), note=metadata.get("note", ""),
            tenue_par=metadata.get("tenue_par") or types[card_type].get("tenue_par"),
            serrure=serrure, num=str(number), a_verifier=bool(metadata.get("a_verifier")),
            sources=metadata.get("sources") or [], path=str(path),
        ))
    cards.sort(key=lambda c: ordre.index(c.type) if c.type in ordre else 99)
    return cards


@dataclass
class Card:
    id: str
    type: str
    section: str                 # "1".."8", "P" ou "J"
    titre: str
    texte: str = ""
    note: str = ""
    tenue_par: str | None = None
    serrure: list[str] = field(default_factory=list)
    num: str = ""                # ce qui s'affiche dans la pastille numéro
    a_verifier: bool = False
    sources: list[str] = field(default_factory=list)
    # champs propres à certains types
    relie: list[int] = field(default_factory=list)
    chauffeur: str = ""
    mathematicien: str = ""
    vierge: bool = False
    lignes: int = 0
    consigne: str = ""
    path: str = ""


@dataclass
class Section:
    key: str
    theme: str
    intention: str
    numero: int | None = None


@dataclass
class Deck:
    config: dict[str, Any]
    types: dict[str, dict[str, Any]]
    ordre: list[str]
    sections: list[Section]
    cards: list[Card]

    def by_id(self) -> dict[str, Card]:
        return {c.id: c for c in self.cards}

    def section_cards(self, key: str) -> list[Card]:
        return [c for c in self.cards if c.section == key]


def load(root: Path, language: str = "fr") -> Deck:
    content = root / "content"
    config = yaml.safe_load((content / "deck.yaml").read_text(encoding="utf-8"))
    config_translations = config.pop("translations", {})
    config = merge_config(config, config_translations.get(language, {}))
    ui = yaml.safe_load((content / "ui.yaml").read_text(encoding="utf-8"))
    config["ui"] = ui[language]
    tdoc = yaml.safe_load((content / "types.yaml").read_text(encoding="utf-8"))
    types = {t["code"]: localized_fields(t, language) for t in tdoc["types"]}
    ordre = tdoc["ordre_dans_famille"]

    sections: list[Section] = []
    cards: list[Card] = []

    # Famille, intention et cartes thématiques sont réunies dans un seul fichier.
    for folder in sorted(p for p in (content / "familles").iterdir() if p.is_dir()):
        fm, intent = read_md(folder / "_famille.md")
        fm = localized_fields(fm, language)
        n = int(fm["numero"])
        intention = re.match(r"(?ms)^## Intention\s*\n(.*?)(?=^## Carte [A-Za-z0-9-]+\s*$|\Z)", intent)
        if intention:
            intent = intention.group(1).strip()
        intent = fm.get("intention", intent)
        sections.append(Section(key=str(n), theme=fm["theme"], intention=intent, numero=n))
        fam_path = folder / "_famille.md"
        fam_cards = read_family_cards(fam_path.relative_to(root), read_md(fam_path)[1], n, types, ordre, language)
        cards += fam_cards

    # Ponts
    sp = config["sections"]["ponts"]
    sections.append(Section(key="P", theme=sp["theme"], intention=sp["intention"]))
    ponts = []
    for f in sorted((content / "ponts").glob("*.md")):
        fm, body = read_md(f)
        fm = localized_fields(fm, language)
        relie = fm.get("relie") or []
        vierge = bool(fm.get("vierge"))
        serrure = fm.get("serrure")
        if serrure is None:
            serrure = [] if vierge else [f"{x}M" for x in relie]
        ponts.append(Card(
            id=fm["id"], type="P", section="P", titre=fm["titre"], texte=fm.get("text", body),
            note=fm.get("note", ""), tenue_par=fm.get("tenue_par") or types["P"].get("tenue_par"),
            serrure=serrure, num="…" if vierge else "·".join(str(x) for x in relie),
            relie=relie, chauffeur=fm.get("chauffeur", ""), mathematicien=fm.get("mathematicien", ""),
            vierge=vierge, consigne=fm.get("consigne", ""), a_verifier=bool(fm.get("a_verifier")),
            path=str(f.relative_to(root)),
        ))
    ponts.sort(key=lambda c: (c.vierge, c.relie, c.id))
    cards += ponts

    # Enjeux
    se = config["sections"]["enjeux"]
    sections.append(Section(key="J", theme=se["theme"], intention=se["intention"]))
    for f in sorted((content / "enjeux").glob("*.md")):
        fm, body = read_md(f)
        fm = localized_fields(fm, language)
        cards.append(Card(
            id=fm["id"], type="J", section="J", titre=fm["titre"], texte=fm.get("text", body),
            note=fm.get("note", ""), tenue_par=fm.get("tenue_par"), serrure=fm.get("serrure") or [],
            num="?", lignes=int(fm.get("lignes", 3)), consigne=fm.get("consigne", ""),
            path=str(f.relative_to(root)),
        ))

    return Deck(config=config, types=types, ordre=ordre, sections=sections, cards=cards)
