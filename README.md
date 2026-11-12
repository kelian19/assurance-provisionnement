# Clair · Provisionnement et incertitude

Outil métier **Python / Streamlit / Plotly** : import d'un triangle, Chain-Ladder, erreur de prédiction de Mack, bootstrap ODP, validation rétrospective et exports traçables.

Le moteur et l'interface sont réalisés. **Démonstration locale uniquement : aucun site n'a été déployé et aucun post LinkedIn n'a été publié.**

## Démarrage

Python 3.12 recommandé. Depuis la racine du dépôt :

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pipeline.prepare_data
.venv/bin/streamlit run app.py
```

Sous Windows, remplacer `.venv/bin/` par `.venv\Scripts\`. Ouvrir l'adresse locale affichée par Streamlit.

Les données du cours sont téléchargées explicitement par prepare_data, jamais à l'ouverture d'une page. Les exemples RAA, GenIns et CAS/NAIC proviennent de la version figée de chainladder. Les fichiers bruts sont exclus de Git et vérifiés par empreinte.

## Résultats déterministes vérifiés

| Jeu | Développement futur estimé | RMSEP Mack |
|---|---:|---:|
| Triangle du cours | **18 680 847,767812435** | **2 447 093,029340** |
| GenIns bibliothèque | 18 680 855,611924 | 2 447 094,860835 |
| RAA | 52 135,228261 | 26 909,011156 |
| CAS/NAIC · State Farm · ppauto | 12 586 821,363383 | 550 736,264265 |

Les résultats sont exprimés dans l'unité de chaque source ; ils ne sont pas automatiquement des euros. Le cas CAS/NAIC est un seul groupe et une seule branche, sans agrégation susceptible de doubler groupes et entités.

La comparaison indépendante avec chainladder utilise exactement le même triangle, pondération par volume, variance finale « Mack » et queue égale à 1. Les écarts numériques sont inférieurs à 10⁻⁶ unité. Le cours et GenIns diffèrent de 4 unités en une cellule : cette différence est conservée, pas « corrigée » pour obtenir artificiellement la même référence.

## Parcours métier

1. Choisir un exemple ou importer un CSV carré annuel `origin,D1,D2,…,Dn`.
2. Confirmer nature, unité et date d'évaluation. NA futurs vides ; montants avec point décimal et sans séparateurs de milliers. Années numériques croissantes et consécutives.
3. Consulter triangle observé/projeté, ultimes, provisions par origine et erreur Mack.
4. Lancer, si les données le permettent, le bootstrap à graine et nombre de simulations explicites.
5. Examiner les diagonales masquées, les réserves méthodologiques et exporter le dossier JSON, les résultats ou les scénarios CSV.

Le calculateur conserve les observations. Sur paiements, l'estimation est un restant à payer ; sur charges encourues, c'est un développement futur de charge. Sans nature confirmée, il utilise un libellé neutre.

L'interface conserve les données importées uniquement en mémoire de session. Aucune donnée client n'est écrite automatiquement sur disque. Les exports sont créés à la demande. Les résultats aléatoires ne sont affichés que pour le triangle et les métadonnées auxquels ils correspondent.

## Bootstrap et limites

Le modèle livré est un **bootstrap ODP de bibliothèque avec processus Gamma signé**, distinct du bootstrap Mack du cours. Les valeurs signées, limites, versions et graines sont affichées et exportées. Un correctif déterministe du levier h=1 évite un défaut de mémoire non initialisée observé dans chainladder 0.10.1.

Les reprises négatives sont conservées pour Mack, mais le bootstrap ODP de cette V1 est refusé si les incréments observés sont négatifs. Les scénarios invalides ne sont pas supprimés silencieusement. Les quantiles ne constituent ni un SCR à un an ni une provision réglementaire approuvée.

[Algorithmes et formules](docs/METHODOLOGIE.md) · [Rapport de validation](reports/RESULTATS.md) · [Résultats numériques](reports/validation.json) · [Sources et empreintes](reports/data_manifest.json)

## Reproduire et tester

```sh
.venv/bin/python -m pytest tests -q
.venv/bin/python -m pipeline.validate_project
```

Le pipeline de validation reproduit les comparaisons, trois diagonales masquées par jeu et 5 000 simulations à graine 42 pour le cours et le cas CAS. Les scénarios complets générés restent hors Git ; les statistiques et diagnostics sont versionnés.

Les tests couvrent les références, la covariance totale, l'homogénéité d'échelle, les erreurs d'entrée, la reproductibilité bootstrap, le risque de processus, l'absence de fuite dans les diagonales masquées et les interactions Streamlit.

La validation R facultative est dans `references/validate_mack.R`. Elle n'a pas été exécutée dans l'environnement de réalisation, où Rscript était absent. La comparaison exécutée utilise l'implémentation Python indépendante de chainladder, aux mêmes options.

## Organisation

- `reserving/` : moteur déterministe, bootstrap, lecture, validation et export, sans dépendance à Streamlit.
- `app.py` : interface métier locale.
- `pipeline/` : récupération et validation reproductibles.
- `tests/` : tests actuariels et parcours de l'interface.
- `reports/` : résultats constatés, sources et limites.
- `docs/` : plan, méthodologie et brouillon LinkedIn.

Schnieper et inflation restent des extensions. Avant une exploitation compagnie, il faut valider le périmètre des données, l'échelle monétaire, la stabilité du développement et la queue, puis obtenir une revue actuarielle indépendante.

## Note méthodologique à partager

[PDF — méthodes et mathématiques](docs/latex/note_provisionnement.pdf) · [Source LaTeX](docs/latex/note_provisionnement.tex).
