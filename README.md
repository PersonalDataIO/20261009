# Chauffeurs et mathématiciens : huit familles

Générateur du jeu de cartes d’atelier. Le contenu, les gabarits et le code sont séparés :
on modifie une carte dans un fichier Markdown, on relance la construction, on obtient
une page HTML autonome avec la vue **Partie** (interactive) et la vue **Impression** (A4).

## Démarrer

```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python build.py            # contrôle puis construit dist/index.html
```

Dans VS Code : `Ctrl+Shift+B` lance la tâche « Jeu : construire ».
Ouvrir ensuite `dist/index.html` dans un navigateur (ou avec Live Server).

## Déployer sur Netlify

Importer le dépôt dans Netlify en gardant la racine du dépôt comme base.
`netlify.toml` installe les dépendances Python, exécute `python build.py` et
publie le dossier `dist/`. Aucun framework ni commande supplémentaire n’est requis.

## Organisation

```
content/                  ← tout le texte du jeu, rien d'autre
  deck.yaml               titre, chapeau, phases, tri des contraintes, détenteurs, consignes d'impression
  types.yaml              les 10 types de cartes : lettre, niveau, détenteur, serrure par défaut
  familles/NN-slug/
    _famille.md           numéro, thème, intention et les huit cartes de la famille
  ponts/                  Ponts imprimés (relie, chauffeur, mathematicien) et Ponts vierges
  enjeux/                 les deux Enjeux secrets
templates/
  card.html.j2            gabarit des cartes : macros recto(), verso(), key()
  print.html.j2           gabarit d'impression : légende, planches, fiche animateur, registre des conflits
  page.html.j2            la page complète (en-tête, onglets, vue Partie) qui inclut print.html.j2
static/
  style.css               style partagé (carte 63 × 88 mm, pages A4, vue Partie)
  play.js                 état de la table et déverrouillage (aucun texte de carte ici)
deckgen/
  loader.py               lit content/ et construit le modèle (Card, Section, Deck)
  validate.py             contrôles : serrures, doublons, types, ponts, cycles, notes, sources
  render.py               Jinja + typographie française ; produit le HTML autonome
  graph.py                graphe des dépendances au format Mermaid
build.py                  colle le tout
dist/                     sortie : index.html, dependances.md, cartes.json
```

## Format d’une famille

Chaque famille se trouve dans un seul fichier `_famille.md`. Le front matter donne
son numéro et son thème ; le corps commence par l’intention, puis contient une
section par carte. Chaque section a un bloc YAML pour les métadonnées et le texte
qui suit est imprimé sur la carte :

````markdown
---
numero: 4
theme: "Preuve"
---

## Intention
Quelle preuve est assez solide pour agir ensemble ?

## Carte 4C
```yaml
type: C                 # T R Qc Qm C E M L
titre: "Chaque camp a sa méthode"
note: "À trier. Désaccord de méthode : il appelle une preuve plus solide."
a_verifier: true        # avertit si aucune source n'est renseignée
sources: []             # URL ou références
# tenue_par: mixte      # facultatif : remplace le détenteur du type
# serrure: [4M, 4C]     # facultatif : remplace la serrure du type
```
Texte de la carte, tel qu'il s'imprime.
````

La serrure par défaut vient de `types.yaml` et s’applique dans la famille
(`E: [T, R]` donne `4T + 4R` pour la carte 4E). Un Pont imprimé se verrouille sur
les Motifs des deux familles qu’il `relie`.

Les codes internes des questions restent `Qc` et `Qm` dans les fichiers. À l’écran
et à l’impression, ils s’affichent dans l’ordre demandeur → destinataire : `cQm`
(chauffeurs vers mathématiciens) et `mQc` (mathématiciens vers chauffeurs).

## Modifier

- **Un texte** : éditer le texte sous la section `## Carte <ID>` dans le `_famille.md` concerné.
- **Une famille** : copier un dossier `familles/`, puis modifier ses métadonnées et ses sections de cartes dans `_famille.md`.
- **Un type de carte** : l’ajouter dans `types.yaml` (et dans `ordre_dans_famille`),
  puis ajouter sa section dans le fichier de chaque famille ; le contrôle le signale sinon.
- **L’apparence d’une carte** : `templates/card.html.j2` et la section « Carte » de `static/style.css`.
- **Les pages imprimées** : `templates/print.html.j2`.

`python build.py --check --strict` échoue tant qu’il reste des avertissements :
utile juste avant d’imprimer.

`dist/dependances.md` s’ouvre avec l’aperçu Markdown de VS Code (extension Mermaid) pour voir le graphe des serrures.

Voir `MANQUES.md` pour ce qui reste à faire.
