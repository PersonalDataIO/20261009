# Éléments manquants ou à décider

Le contrôle (`python build.py --check`) en signale une partie automatiquement.

## Contenu à vérifier avant l’atelier

Douze cartes portent `a_verifier: true` et n’ont pas encore de `sources` :
1R, 2L, 4C, 5T, 5C, 6C, 7R, 7Qc, 7C, 7L, 8R, 8C.

- **Faits datés repris du deck précédent** : réfutation d’Erdős (mai 2026), chiffres Oxera
  et contestation d’Uber, procédure d’Amsterdam, article signé « OpenAI », date de
  transposition de la directive sur le travail via plateforme.
- **Droit suisse** : l’équivalent de l’article 22 RGPD (Levier 2L), et l’existence d’une
  réserve contre la fouille de textes en Suisse (7Qc, 7L). À faire relire par un juriste.
- **Licences des éditeurs** (7R) : vérifier les accords connus avant d’en parler.

## Décisions de conception ouvertes

- **Famille 3 (Surveillance) sans Pont imprimé.** Son Levier dépend d’un Pont inventé.
  Candidat : 3·6, « ce que la note ne voit pas » (la note et le vérificateur ignorent ce
  qui fait un bon chauffeur ou une belle idée).
- **Détenteurs** : tout ce qui n’est pas T, R, Qc ou Qm est provisoirement « binôme mixte ».
- **Règle « un Levier exige un Pont »** : appliquée par la table, pas par les serrures.
  Pour la coder, il faudrait une serrure alternative (« un Pont quelconque touchant la
  famille »), que `loader.py` ne gère pas encore.
- **Seuil de victoire** : `leviers_pour_gagner: 4` dans `deck.yaml`, à tester en atelier.
- **Rôles de l’équipe d’animation** (Témoin, Traducteur, Sceptique, Stratège, Plateforme)
  et cartes **Règle** : mis de côté pour l’instant ; ni type ni gabarit.
- **Carte Preuve** pour lever un Désaccord : évoquée dans la mécanique, pas encore de type.

## Matériel physique à produire

- Plateau ou tapis : huit couloirs côte à côte, avec l’emplacement de chaque type.
- Marqueurs de **faux pont** (jetons ou pinces).
- Le **registre des conflits** est généré (dernière page d’impression) ; prévoir un format
  affiche si la salle est grande.
- Feuille de bilan : photo du réseau de Ponts, Leviers ouverts, Enjeux retournés.

## Outillage

- Pas encore d’export de la vue Partie vers un fichier (sauvegarde d’une partie en cours).
- Pas de traduction : tout le texte est en français ; une version anglaise demanderait
  un champ par langue dans les fichiers de cartes.
- `cartes.json` permet de brancher d’autres outils (plateforme multi-communautés, statistiques).
