# Résultats de validation — reserving-v1

## Réconciliation déterministe
| Jeu | Provision / développement futur | RMSEP Mack | Écart réserve bibliothèque | Écart RMSEP bibliothèque |
|---|---:|---:|---:|---:|
| course | 18,680,847.767812 | 2,447,093.029340 | 1.12e-08 | 9.31e-10 |
| genins | 18,680,855.611924 | 2,447,094.860835 | 1.12e-08 | 4.66e-10 |
| raa | 52,135.228261 | 26,909.011156 | 0 | 0 |
| cas | 12,586,821.363383 | 550,736.264265 | 5.59e-09 | 1.16e-10 |

Les unités sont propres à chaque source. Elles ne sont pas additionnées ou converties en euros. Les facteurs, les RMSEP annuelles et la covariance totale sont aussi testés, avec tolérance numérique stricte.

Le cours et GenIns diffèrent en une cellule de 4 unités. La variance finale est l'approximation de Mack. La référence Python utilise la même option ; Rscript étant absent, le script R facultatif n'a pas été exécuté et aucune concordance R exécutée n'est revendiquée.

## Bootstrap du cours
5 000 simulations, graine 42, risque de processus ajouté avec graine 43. Modèle ODP de bibliothèque avec correction déterministe du levier et processus Gamma signé, distinct de Mack.

| Indicateur | Montant dans l'unité du cours |
|---|---:|
| Moyenne | 18,840,414.38 |
| Médiane | 18,652,950.34 |
| Écart-type | 2,945,899.68 |
| Quantile 95 % | 24,138,111.42 |
| Quantile 99 % | 26,805,701.39 |
| Erreur Monte-Carlo de la moyenne | 41,661.31 |

444 scénarios sur 5000 contiennent des incréments futurs moyens négatifs ; ils sont conservés avec l'extension Gamma signée. 0 réserves totales simulées sont négatives. 0 simulation invalide est supprimée. Les Q95 sur quatre lots sont [23857137.49110127, 24422364.33908906, 24135555.11332142, 24280912.428492364]. Ces lots sont un diagnostic Monte-Carlo et non un intervalle de confiance.

La moyenne bootstrap diffère du point Chain-Ladder : les hypothèses, le rééchantillonnage et l'erreur Monte-Carlo interviennent. Les écarts-types Mack et ODP sont ceux de modèles distincts, sans exigence d'égalité artificielle.

## Cas réel CAS/NAIC
Périmètre figé : State Farm Mut Grp, ppauto, CumPaidLoss, origines 1988–1997, évaluation fin 1997. Les valeurs restent dans l'unité de la source ; l'application ne suppose aucune conversion monétaire.

Moyenne bootstrap : 12,593,761.86 ; Q95 : 13,420,775.66 ; Q99 : 13,764,890.42. 721 scénarios contiennent des moyens futurs négatifs, explicitement conservés par le processus signé.

## Diagonales masquées
Le ratio observé/prédit porte sur les incréments de la diagonale suivante des origines existantes, hors dernière maturité et nouvelle origine. Les facteurs sont réestimés à chaque arrêt, sans utiliser les observations masquées.

| Jeu | Dernière diagonale masquée | Arrêt précédent | Troisième arrêt |
|---|---:|---:|---:|
| course | 115.30 % | 109.86 % | 74.75 % |
| genins | 115.30 % | 109.86 % | 74.75 % |
| raa | 67.35 % | 119.99 % | 116.43 % |
| cas | 86.77 % | 85.88 % | 89.53 % |

Les résultats défavorables sont conservés. Sur le cas CAS, les ratios inférieurs à 1 signalent une surestimation des incréments des diagonales masquées. Trois arrêts sur un seul triangle ne constituent pas une validation générale des provisions ultimes.

## Tests et vérifications
- Référence numérique du cours et comparaison à une bibliothèque indépendante sur quatre triangles.
- Observations préservées, covariance interannuelle incluse et homogénéité d'échelle.
- Erreurs de format, futur rempli par zéro, trous, cumuls nuls et ordre des années contrôlés.
- Reproductibilité à graine identique et correctif h=1 testé explicitement.
- Présence du risque de processus et refus des simulations non finies ; refus ODP pour incréments observés négatifs.
- Test d'absence de fuite dans les prédictions de diagonales masquées.
- Tests Streamlit : affichage de référence, simulation, changement de source sans résultat périmé et erreur explicite sur RAA pour le bootstrap.

Les avertissements de dépréciation pandas émis par chainladder sont conservés dans les diagnostics. Ils ne sont pas des suppressions de simulations. Le test de mémoire non initialisée a entraîné un correctif ciblé documenté ; les résultats finaux sont ceux obtenus après ce correctif.

## Décision
V1 locale utilisable comme démonstrateur actuariel vérifié. Aucune approbation de provision compagnie ou de capital réglementaire n'est revendiquée. Avant exploitation : revoir les sources, la nature des montants, les unités, les changements de cadence, l'inflation et la queue. Aucune publication ou mise en ligne publique n'a été réalisée.
