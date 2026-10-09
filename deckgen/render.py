"""Rendu HTML : gabarits Jinja (templates/) + style et script (static/)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

from .loader import Deck


def typo(s: str, language: str = "fr") -> Markup:
    """Espaces fines insécables de la typographie française."""
    s = s or ""
    if language != "fr":
        return Markup(s)
    s = re.sub(r" ([:;?!»%€])", "\u202F\\1", s)
    s = s.replace("« ", "«\u202F")
    s = re.sub(r"(\d) (?=\d{3}\b)", "\\1\u202F", s)
    return Markup(s)


def chunks(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]


def mirror_rows(cells, cols=3):
    """Verso d'une planche : chaque rangée est inversée (retournement sur le bord long)."""
    out = []
    for r in range(0, len(cells), cols):
        out += list(reversed(cells[r:r + cols]))
    return out


def make_env(root: Path, deck: Deck, language: str) -> Environment:
    env = Environment(loader=FileSystemLoader(root / "templates"), autoescape=False,
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    env.filters["t"] = lambda text: typo(text, language)
    env.filters["chunks"] = chunks
    env.filters["mirror_rows"] = mirror_rows
    env.globals.update(
        deck=deck, cfg=deck.config, types=deck.types, ui=deck.config["ui"], language=language,
        holders=deck.config["detenteurs"], levels={int(k): v for k, v in deck.config["niveaux"].items()},
    )
    return env


def build_html(root: Path, deck: Deck, language: str = "fr") -> str:
    env = make_env(root, deck, language)
    labels = {"fr": ("Télécharger la vidéo", "Vidéos des familles"),
              "en": ("Download video", "Family videos")}[language]
    video_prefix = "videos/" if language == "fr" else "../videos/"
    family_videos = {str(section.numero): video_prefix + Path(next(
        (root / "content/familles").glob(f"{section.numero:02}-*"))).name
        + ("-en" if language == "en" else "") + ".mp4"
        for section in deck.sections if section.numero is not None}
    card = env.get_template("card.html.j2").module
    play_data = {
        "sections": [{"key": s.key, "theme": str(typo(s.theme, language)), "intention": str(typo(s.intention, language)),
                      "video": family_videos.get(s.key)} for s in deck.sections],
        "cards": [{
            "id": c.id, "section": c.section, "type": c.type, "lock": c.serrure,
            "recto": str(card.recto(c)), "verso": str(card.verso(c)), "note": str(typo(c.note, language)),
        } for c in deck.cards],
        "leviers": {"total": sum(1 for c in deck.cards if c.type == "L"),
                "pour_gagner": deck.config["leviers_pour_gagner"]},
        "ui": deck.config["ui"],
        "video_download_label": labels[0],
    }
    page = env.get_template("page.html.j2")
    return page.render(
        css=(root / "static" / "style.css").read_text(encoding="utf-8"),
        js=(root / "static" / "play.js").read_text(encoding="utf-8"),
        data=json.dumps(play_data, ensure_ascii=False).replace("</", "<\\/"),
        language=language,
        language_switch_href="en/" if language == "fr" else "../",
        family_videos=family_videos, video_download_label=labels[0], video_heading=labels[1],
    )
