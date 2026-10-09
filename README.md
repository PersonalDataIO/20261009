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
publie le dossier `dist/`. Le build crée le site français à `/` et l’anglais à
`/en/`. Aucun framework ni commande supplémentaire n’est requis.

## Langues

Le français est la langue source. Les traductions sont stockées près de leur
contenu dans une map `translations`, indexée par code de langue. Le thème et
l’intention d’une famille se traduisent dans son front matter; pour chaque carte,
`titre`, `note` et `text` se traduisent dans son bloc YAML. Ponts et Enjeux
utilisent la même map dans leur front matter. Les libellés partagés de l’interface
et de l’impression sont dans `content/ui.yaml`; les phases, sections et consignes
globales sont traduites dans `content/deck.yaml`. `python build.py` valide et
génère les deux langues à partir des mêmes gabarits.

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

## Vidéos courtes

Les huit familles ont des storyboards en français et en anglais. Les vidéos présentent une explication du but du jeu,
deux témoignages, un Écho, les deux questions dirigées, un levier et un appel final
« Explore the game! ». Le format vertical 1080 × 1920 fonctionne sans son, avec
du texte intégré à l'image. Le rendu vidéo est indépendant de `build.py` et de Netlify.
Les liens de téléchargement se trouvent dans « Vidéos des familles » en tête de page
et sous chaque titre de famille. Ils ciblent toujours la langue de la page.
Les MP4 finalisés sont conservés dans `public/videos/` ; `build.py` les copie
dans `dist/videos/` pour les publier aussi sur Netlify, sans réencodage.
Flair inclut aussi sa Contrainte. Chaque carte montre son titre et son texte complets,
sans indice, avec une petite boîte de type au-dessus. Les questions indiquent
explicitement leur expéditeur et leur destinataire. Les notes d'animation ne sont
pas affichées. La durée de chaque carte est au moins celle du storyboard, allongée
si nécessaire pour laisser trois secondes de transition et 150 mots/minute de lecture.

Installation facultative, avec FFmpeg disponible dans le `PATH` :

```bash
pip install -r requirements-video.txt
python -m playwright install chromium
# macOS, si nécessaire : brew install ffmpeg
python video.py --draft
```

Pour produire toutes les vidéos publiques et actualiser les fichiers publiables :

```bash
python video.py --all --language both --out public/videos
python build.py
```

Le rendu réutilise les images fixes pendant la lecture et conserve les transitions
animées. La progression avance au changement de scène.

Les fichiers sont générés dans `dist/videos/` : MP4 H.264 à 24 images/seconde,
affiche PNG, aperçu HTML animé, sous-titres SRT et storyboard JSON. L'aperçu HTML
s'ouvre directement dans un navigateur, sans serveur. Les polices Google demandent
une connexion Internet ; sans accès réseau, le navigateur utilise les polices de secours.
L'aperçu respecte la préférence de réduction des animations.

```bash
python video.py --draft --preview-only  # aperçu sans Chromium ni FFmpeg
python video.py --draft --width 540     # export léger
python -m unittest discover -s tests -p 'test_video.py'
```

Le storyboard éditorial vit dans `content/videos/01-flair.yaml`. Une scène indique
sa durée minimale, son type (`intro`, `driver`, `researcher`, `echo`, `question`,
`tension`, `action`) et éventuellement l'identifiant d'une carte. Pour une scène
de carte, le titre et le texte sont toujours repris intégralement du jeu, dans
la langue choisie. `text` et `detail` restent disponibles pour les scènes sans carte.

`content/videos/framing.yaml` fournit les scènes communes d'ouverture (8 secondes)
et de conclusion (12 secondes), en français et en anglais. L'ouverture explique
le rapprochement des perspectives des chauffeurs Uber et des mathématiciens face
à l'IA. Ces scènes sont ajoutées automatiquement à chaque storyboard.

La variable d'environnement `HOST_URL` fixe la destination de l'appel final et
des liens de l'aperçu. Par défaut : `https://20261009.personaldata.io/`.
L'adresse est visible dans le MP4 ; les liens sont cliquables dans l'aperçu HTML.
Elle remplace le champ `url` des anciens storyboards lors du rendu.

```bash
HOST_URL=https://20261009.personaldata.io/ python video.py --story content/videos/07-droits.yaml --draft
```

Les cartes marquées `a_verifier` bloquent un export public tant que la scène
correspondante n'a pas `verified: true`, après vérification éditoriale réelle.
`--draft` permet la relecture avec un marquage visible et un nom de fichier distinct.
Les cartes des huit familles ont été vérifiées. Pour un export sans marquage :

```bash
python video.py
```

Pour une autre famille, créer un storyboard avec son numéro `family`, un `slug`
unique et ses scènes, puis lancer :

```bash
python video.py --story content/videos/02-boite-noire.yaml --draft
```

Les huit storyboards sont fournis en français et en anglais.
Pour exporter la famille 7 :

```bash
python video.py --story content/videos/07-droits.yaml --draft
python video.py --story content/videos/07-droits.yaml --language en --draft
```

Les familles 2 à 6 et 8 présentent leurs huit cartes dans l'ordre
Terrain, Recherche, Écho, Questions, Motif, Contrainte et Levier. Les séquences
éditoriales existantes de Flair et Droits sont conservées.
