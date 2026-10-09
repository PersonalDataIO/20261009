"""Contrôles de cohérence du contenu, avant tout rendu."""
from __future__ import annotations

from .loader import Deck

REQUIRED = ("id", "type", "titre")


def validate(deck: Deck) -> tuple[list[str], list[str]]:
    """Retourne (erreurs, avertissements)."""
    errors: list[str] = []
    warnings: list[str] = []
    ids = [c.id for c in deck.cards]
    known = set(ids)

    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"Identifiant en double : {dup}")

    holders = set(deck.config["detenteurs"])
    for c in deck.cards:
        where = f"{c.id} ({c.path})"
        for k in REQUIRED:
            if not getattr(c, k):
                errors.append(f"{where} : champ « {k} » manquant")
        if c.type not in deck.types:
            errors.append(f"{where} : type inconnu « {c.type} »")
        for k in c.serrure:
            if k not in known:
                errors.append(f"{where} : la serrure cite {k}, qui n’existe pas")
            if k == c.id:
                errors.append(f"{where} : la carte se verrouille elle-même")
        if c.tenue_par not in holders:
            errors.append(f"{where} : détenteur « {c.tenue_par} » absent de deck.yaml")
        if c.type == "P" and not c.vierge:
            if len(c.relie) != 2 or c.relie[0] == c.relie[1]:
                errors.append(f"{where} : un Pont relie exactement deux familles différentes")
            if not (c.chauffeur and c.mathematicien):
                errors.append(f"{where} : un Pont imprimé a besoin des deux moitiés")
        if not c.note and c.type not in ("P", "J"):
            warnings.append(f"{where} : pas de note animateur")
        if c.a_verifier and not c.sources:
            warnings.append(f"{where} : à vérifier, aucune source renseignée")

    # Chaque famille doit avoir exactement un exemplaire de chaque type prévu
    for s in deck.sections:
        if s.numero is None:
            continue
        got = sorted(c.type for c in deck.section_cards(s.key))
        if got != sorted(deck.ordre):
            errors.append(f"Famille {s.key} : types {got}, attendu {sorted(deck.ordre)}")

    # Chaque famille devrait être touchée par au moins un Pont imprimé
    touched = {x for c in deck.cards if c.type == "P" for x in c.relie}
    for s in deck.sections:
        if s.numero is not None and s.numero not in touched:
            warnings.append(f"Famille {s.key} ({s.theme}) : aucun Pont imprimé ne la touche ; son Levier dépendra d’un pont inventé")

    # Cycles de serrures (une carte ne doit pas pouvoir se bloquer indirectement)
    graph = {c.id: c.serrure for c in deck.cards}
    state: dict[str, int] = {}

    def visit(n: str, path: list[str]) -> None:
        if state.get(n) == 1:
            errors.append("Cycle de serrures : " + " → ".join(path + [n]))
            return
        if state.get(n) == 2 or n not in graph:
            return
        state[n] = 1
        for m in graph[n]:
            visit(m, path + [n])
        state[n] = 2

    for n in graph:
        visit(n, [])
    return errors, warnings
