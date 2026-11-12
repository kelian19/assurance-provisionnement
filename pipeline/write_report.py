"""Rédige les documents de résultats uniquement à partir de la validation mesurée."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 r=json.loads((ROOT/'reports/validation.json').read_text(encoding='utf-8'));course=r['bootstrap']['course'];cas=r['bootstrap']['cas'];a=course['summary'];c=course['diagnostics']
 rows='\n'.join(f"| {v['dataset']} | {v['reserve']:,.6f} | {v['mack_rmsep']:,.6f} | {v['absolute_reserve_gap']:.3g} | {v['absolute_rmsep_gap']:.3g} |" for v in r['deterministic_comparisons'])
 text=f'''# Résultats de validation — reserving-v1

## Réconciliation déterministe
| Jeu | Provision / développement futur | RMSEP Mack | Écart réserve bibliothèque | Écart RMSEP bibliothèque |
|---|---:|---:|---:|---:|
{rows}

Les unités sont propres à chaque source. Elles ne sont pas additionnées ou converties en euros. Les facteurs, les RMSEP annuelles et la covariance totale sont aussi testés, avec tolérance numérique stricte.

Le cours et GenIns diffèrent en une cellule de 4 unités. La variance finale est l'approximation de Mack. La référence Python utilise la même option ; Rscript étant absent, le script R facultatif n'a pas été exécuté et aucune concordance R exécutée n'est revendiquée.

## Bootstrap du cours
5 000 simulations, graine 42, risque de processus ajouté avec graine 43. Modèle ODP de bibliothèque avec correction déterministe du levier et processus Gamma signé, distinct de Mack.

| Indicateur | Montant dans l'unité du cours |
|---|---:|
| Moyenne | {a['mean']:,.2f} |
| Médiane | {a['median']:,.2f} |
| Écart-type | {a['std']:,.2f} |
| Quantile 95 % | {a['q95']:,.2f} |
| Quantile 99 % | {a['q99']:,.2f} |
| Erreur Monte-Carlo de la moyenne | {a['mean_monte_carlo_se']:,.2f} |

{c['negative_mean_simulations']} scénarios sur {c['simulations']} contiennent des incréments futurs moyens négatifs ; ils sont conservés avec l'extension Gamma signée. {c['negative_reserve_simulations']} réserves totales simulées sont négatives. {c['invalid_simulations_discarded']} simulation invalide est supprimée. Les Q95 sur quatre lots sont {c['q95_batches']}. Ces lots sont un diagnostic Monte-Carlo et non un intervalle de confiance.

La moyenne bootstrap diffère du point Chain-Ladder : les hypothèses, le rééchantillonnage et l'erreur Monte-Carlo interviennent. Les écarts-types Mack et ODP sont ceux de modèles distincts, sans exigence d'égalité artificielle.

## Cas réel CAS/NAIC
Périmètre figé : State Farm Mut Grp, ppauto, CumPaidLoss, origines 1988–1997, évaluation fin 1997. Les valeurs restent dans l'unité de la source ; l'application ne suppose aucune conversion monétaire.

Moyenne bootstrap : {cas['summary']['mean']:,.2f} ; Q95 : {cas['summary']['q95']:,.2f} ; Q99 : {cas['summary']['q99']:,.2f}. {cas['diagnostics']['negative_mean_simulations']} scénarios contiennent des moyens futurs négatifs, explicitement conservés par le processus signé.

## Diagonales masquées
Le ratio observé/prédit porte sur les incréments de la diagonale suivante des origines existantes, hors dernière maturité et nouvelle origine. Les facteurs sont réestimés à chaque arrêt, sans utiliser les observations masquées.

| Jeu | Dernière diagonale masquée | Arrêt précédent | Troisième arrêt |
|---|---:|---:|---:|
'''
 for key in ['course','genins','raa','cas']:
  ratios=[v['observed_predicted'] for v in r['backtests'][key]]
  text+=f"| {key} | "+' | '.join(f'{100*v:.2f} %' for v in ratios)+' |\n'
 text+='''
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
'''
 (ROOT/'reports/RESULTATS.md').write_text(text,encoding='utf-8')
 post=f'''# Brouillon LinkedIn — non publié

J’ai construit un outil de provisionnement en Python, avec une interface Streamlit pour passer du triangle à une estimation expliquée.

La première étape a été de reproduire le montant du cours : 18 680 847,77 unités de développement futur estimé. L’erreur de prédiction de Mack vaut 2 447 093,03 unités, soit environ 13,1 % de cette estimation.

Le moteur a ensuite été comparé à une bibliothèque actuarielle indépendante sur le triangle du cours, RAA, GenIns et un périmètre CAS/NAIC.

Pour explorer l’incertitude, j’ai ajouté un bootstrap ODP avec risque de processus. Sur 5 000 scénarios à graine fixée, le quantile à 95 % vaut {a['q95']:,.2f} unités sur le triangle du cours. Ce résultat dépend des hypothèses du bootstrap, dont une extension Gamma signée explicitement documentée ; ce n’est pas un quantile Mack ni un SCR à un an.

Les résultats de validation rétrospective restent visibles même lorsqu’ils sont défavorables. L’outil distingue calcul vérifié et hypothèses à valider sur le portefeuille.

Code, méthodes, résultats et guide local : https://github.com/kelian19/assurance-provisionnement

#Actuariat #Provisionnement #Python #Assurance
'''
 (ROOT/'docs/POST_LINKEDIN_PROVISIONNEMENT.md').write_text(post,encoding='utf-8')
 print('Rapport et brouillon LinkedIn produits depuis les résultats mesurés.')
if __name__=='__main__':main()
