# Résultats Schnieper — exemple 5.4 du cours

Données : https://nicolasbaradel.fr/enseignement/ressources/R/donneesSCHNIEPER_{N,D,E}.txt (unités du cours, non précisées). Modèle et estimateurs : cours de N. Baradel §5, bootstrap §6.4.1.

| Année | Dernier cumul | Ultime | Provision | dont vrais IBNR | dont IBNER | Écart-type de processus | Mack |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 79.5 | 79.5 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 2 | 60.0 | 64.4 | 4.4 | 6.4 | -2.0 | 0.0 | 2.0 |
| 3 | 96.5 | 101.3 | 4.8 | 14.7 | -9.9 | 7.4 | 4.6 |
| 4 | 46.9 | 79.8 | 32.9 | 37.7 | -4.8 | 23.6 | 17.2 |
| 5 | 52.7 | 113.0 | 60.3 | 64.5 | -4.2 | 32.3 | 52.6 |
| 6 | 29.4 | 106.6 | 77.2 | 83.1 | -5.9 | 35.3 | 80.8 |
| 7 | 19.1 | 123.4 | 104.3 | 104.7 | -0.4 | 39.4 | 306.9 |
| **Total** | | 668.0 | **283.9** | 311.1 | -27.2 | 66.8 | 464.2 |

Reproduction des valeurs imprimées dans le cours : λ, δ, σ, τ, ultimes, provisions par année, total 283,9 et Mack 464,2 sont identiques à l'arrondi du cours (écart maximal 0e+00). L'exemple 5.6 (nombres au-dessus d'un seuil, total 7,97) est testé dans `tests/test_schnieper.py`.

## Bootstrap non paramétrique (5000 scénarios, graine 42)
Moyenne 283.7 (99.9 % de l'estimation), médiane 280.1, écart-type 109.0 (paramètres seuls 84.2), Q95 464.0, Q99 549.8. 93 scénarios sur 5000 (1.86 %) contiennent un cumul négatif ramené à zéro, comme le `pmax` du cours ; ils sont conservés. L'écart-type du bootstrap est cohérent avec la somme quadratique de l'erreur de paramètres seule et de la variance de processus analytique.

## Limites
- Variance analytique : processus seul. σ²_n = τ²_{n−1} = 0 par convention du cours : l'année 2 (une seule cellule future) a une variance nulle, ce qui sous-estime son risque.
- Un seul triangle pédagogique de 7 années ; aucune validation rétrospective possible sans autre jeu N/D/E.
- La Table 6 du cours (écart-type relatif ≈ 43 %) n'est pas reproduite : le texte du cours la rattache à un jeu de données ambigu (§5.6 ou §5.4). Notre bootstrap sur l'exemple 5.4 donne 38 %.
- Aucune inflation, aucun facteur de queue, aucune actualisation ; pas de SCR à un an.
