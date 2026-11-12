# Note méthodologique — provisionnement

- `note_provisionnement.tex` : source LaTeX.
- `note_provisionnement.pdf` : version compilée, sept pages A4, avec quatre figures.
- `figures/*.pdf` : figures vectorielles, générées par `python -m pipeline.make_figures` (après `python -m pipeline.prepare_data`). Le bootstrap du cours est rejoué (5 000 scénarios, graine 42) et comparé aux statistiques de `reports/calculation_course.json` ; la génération échoue si elles diffèrent.

Compilation (deux passes pour la pagination ; le préambule choisit seul les polices selon le moteur) :

```sh
pdflatex -interaction=nonstopmode -halt-on-error note_provisionnement.tex
pdflatex -interaction=nonstopmode -halt-on-error note_provisionnement.tex
```

Le PDF publié a été compilé avec [Tectonic](https://tectonic-typesetting.github.io) (moteur XeTeX) : `tectonic -X compile note_provisionnement.tex`. Les deux moteurs sont acceptés.

Dépendances TeX : classes usuelles, Latin Modern, iftex (fontspec sous XeTeX), babel avec locale française importable, amsmath, graphicx, caption, booktabs, tabularx, microtype, xcolor, tcolorbox, enumitem, fancyhdr, lastpage, titlesec et hyperref. Dépendances Python des figures : `matplotlib`, en plus de `requirements.txt`.

Les formules décrivent les méthodes réellement utilisées. Les exemples d'historique hypothétique sont identifiés comme tels ; les résultats mesurés et les extensions prévues sont distingués. Documents préparés pour accompagner une présentation du projet ; aucune publication LinkedIn effectuée.
