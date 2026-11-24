# Données de départ (référentiels)

Fichiers de graines pour les produits et marchés du MVP. Aucun prix n'est stocké ici : les prix viennent de l'import FAO (statut `en_attente`) ou de la saisie admin.

## Produits (`produits.csv`) — 6 lignes

| code | nom | nom_fpma | touche |
|---|---|---|---|
| mais_blanc | Maïs Blanc | Maïs Blanc | 1 |
| mais_jaune | Maïs Jaune | Maïs Jaune | 2 |
| soja | Soja | Soja | 3 |
| haricot_blanc | Haricot blanc | Haricot blanc | 4 |
| haricot_noir | Haricot noir | Haricot noir | 5 |
| haricot_rouge | Haricot rouge | Haricot rouge | 6 |

Les touches 1 à 6 sont uniques et suivent l'ordre FAO / plan B du projet.

## Marchés (`marches.csv`) — 3 lignes

| code | nom (marché) | commune | nom_fpma |
|---|---|---|---|
| bohicon | Bohicon | Bohicon | Bohicon |
| houndjro | Houndjro (Abomey) | Abomey | Houndjro (Abomey) |
| azogotchebou | Azogotchébou (Covè) | Covè | Azogotchébou (Covè) |

- `nom_fpma` doit rester **identique** au nom FAO (accents compris), caractère pour caractère.
- Le nom du marché n'est **pas** simplement « Abomey » ni simplement « Covè ».
- Le 4e marché n'est **pas décidé** : ne pas ajouter Hlanxi (Zogbodomey) ni d'autre marché inventé.
- Ne pas inclure le marché INStaD nommé « Abomey » (mensuel, hors MVP).

## Rappels

- Pas de colonne `departement` dans `marches.csv`.
- Pas de ligne de prix dans ces fichiers.
- La touche 1 (prix) lit encore le CSV FAO tant que `SOURCE_PRIX=fao`.
