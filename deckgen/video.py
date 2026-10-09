"""Prepare a small, explicitly edited storyboard from the existing deck."""
from __future__ import annotations

import math
import os
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .loader import Deck, Section, localized_fields, read_family_cards, read_md

HOST_URL = "https://20261009.personaldata.io/"


def load_video_deck(root: Path, storyboard: Path, language: str = "fr") -> Deck:
    metadata = yaml.safe_load(storyboard.read_text(encoding="utf-8"))
    number = int(metadata["family"])
    type_doc = yaml.safe_load((root / "content/types.yaml").read_text(encoding="utf-8"))
    types = {item["code"]: localized_fields(item, language) for item in type_doc["types"]}
    order = type_doc["ordre_dans_famille"]
    for path in sorted((root / "content/familles").glob("*/_famille.md")):
        fields, body = read_md(path)
        fields = localized_fields(fields, language)
        if int(fields["numero"]) == number:
            section = Section(key=str(number), theme=fields["theme"], intention="", numero=number)
            cards = read_family_cards(path.relative_to(root), body, number, types, order, language)
            ui = yaml.safe_load((root / "content/ui.yaml").read_text(encoding="utf-8"))[language]
            return Deck(config={"ui": ui}, types=types, ordre=order, sections=[section], cards=cards)
    raise ValueError(f"Unknown family: {number}")


def prepare_story(deck: Deck, path: Path, draft: bool = False, language: str = "fr") -> dict:
    story = yaml.safe_load(path.read_text(encoding="utf-8"))
    translations = story.pop("translations", {})
    story.update(translations.get(language, {}))
    family = str(story["family"])
    section = next((item for item in deck.sections if item.key == family), None)
    if section is None or section.numero is None:
        raise ValueError(f"Unknown family: {family}")
    if not story.get("scenes"):
        raise ValueError("The storyboard needs at least one scene")
    host_url = os.environ.get("HOST_URL", HOST_URL)
    parsed_url = urlsplit(host_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("HOST_URL must be an absolute HTTP or HTTPS URL")
    framing_path = Path(__file__).resolve().parents[1] / "content/videos/framing.yaml"
    framing = yaml.safe_load(framing_path.read_text(encoding="utf-8"))
    cards = deck.by_id()
    elapsed = 0.0
    scenes = []
    for source in [framing["opening"], *story["scenes"], framing["closing"]]:
        scene = {key: value for key, value in source.items() if key != "translations"}
        scene.update((source.get("translations") or {}).get(language, {}))
        duration = float(scene["duration"])
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("Scene durations must be finite and positive")
        card = cards.get(scene.get("card"))
        if scene.get("card") and (card is None or card.section != family):
            raise ValueError(f"Invalid family card: {scene['card']}")
        if card and card.a_verifier and scene.get("verified") is not True and not draft:
            raise ValueError(f"{card.id} requires editorial verification; use --draft for review")
        if scene["kind"] not in {"explanation", "intro", "driver", "researcher", "echo", "question", "tension", "action", "cta"}:
            raise ValueError(f"Unknown scene kind: {scene['kind']}")
        if card:
            participants = {"fr": ("Chauffeurs Uber", "Mathématiciens"),
                            "en": ("Uber drivers", "Mathematicians")}[language]
            sender, recipient = "", ""
            if card.type in {"Qc", "Qm"}:
                sender, recipient = participants if card.type == "Qc" else participants[::-1]
            scene.update(text=card.titre, detail=card.texte,
                         type_name=deck.types[card.type]["nom"],
                         sender=sender, recipient=recipient)
            duration = max(duration, math.ceil(3 + len((card.titre + " " + card.texte).split()) / 2.5))
        scene.update(start=elapsed, end=elapsed + duration,
                     duration=duration,
                     text=scene.get("text", card.titre if card else section.theme),
                     detail=scene.get("detail", ""))
        scenes.append(scene)
        elapsed += duration
    return {**story, "url": host_url, "family": family, "theme": section.theme, "scenes": scenes,
            "duration": elapsed, "draft": draft,
            "language": language, "ui": deck.config["ui"],
            "cards": [{"id": card.id, "title": card.titre} for card in deck.section_cards(family)]}


def render_preview(root: Path, story: dict) -> str:
    env = Environment(loader=FileSystemLoader(root / "templates"),
                      autoescape=True, undefined=StrictUndefined)
    return env.get_template("video.html.j2").render(story=story)


def subtitles(story: dict) -> str:
    def timestamp(seconds: float) -> str:
        milliseconds = round(seconds * 1000)
        hours, remainder = divmod(milliseconds, 3600000)
        minutes, remainder = divmod(remainder, 60000)
        seconds, milliseconds = divmod(remainder, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    separator = ": " if story.get("language") == "en" else " : "
    return "\n\n".join(
        f"{index}\n{timestamp(scene['start'])} --> {timestamp(scene['end'])}\n"
        f"{scene['label']}{separator}{scene['text']}"
        + (f"\n{scene['detail']}" if scene["detail"] else "")
        for index, scene in enumerate(story["scenes"], 1)
    ) + "\n"