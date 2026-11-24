# Incertitude à un an — Merz et Wüthrich (2008)

Erreur de prédiction du **résultat de développement (CDR)** de la prochaine année calendaire, comparée à l’erreur de Mack sur l’ultime. Paramètres de Mack identiques (facteurs pondérés, variance finale « Mack », queue = 1). Généré par `python -m pipeline.merz_wuthrich_report`.

## Contrôle sur le triangle de l’article

| | Article | Moteur |
|---|---:|---:|
| Développement futur total | 2 237 826 | 2 237 826,1 |
| √msep Mack (ultime) | 108 401 | 108 401,4 |
| √msep CDR à un an | 81 080 | 81 080,5 |

Contrôle exact supplémentaire (tests) : pour l’origine à qui il ne reste qu’une période de développement, l’incertitude à un an égale celle de Mack.

## Triangles du projet

| Triangle | Développement futur | √msep Mack (ultime) | √msep CDR à un an | Un an / ultime |
|---|---:|---:|---:|---:|
| Mack — triangle du cours | 18 680 848 | 2 447 093 | 1 778 966 | 73 % |
| GenIns — bibliothèque | 18 680 856 | 2 447 095 | 1 778 968 | 73 % |
| RAA — bibliothèque | 52 135 | 26 909 | 25 182 | 94 % |
| CAS/NAIC — State Farm, auto particuliers | 12 586 821 | 550 736 | 518 502 | 94 % |

Lecture : la part « un an / ultime » indique quelle fraction de l’incertitude totale (en écart-type) se révèle dès l’année calendaire suivante. Elle est élevée quand le développement est rapide.

## Limites

- Horizon d’un an : ne donne pas le SCR, qui demande aussi la marge de risque et une mesure de risque (VaR 99,5 %).
- msep, pas un quantile : passer à un quantile exige une hypothèse de loi.
- Mêmes hypothèses que Mack (indépendance des origines, pas de queue, pas d’inflation).
- Approximation linéaire de Merz-Wüthrich (termes d’ordre supérieur négligés).
