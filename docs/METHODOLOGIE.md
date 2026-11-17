# Méthodologie de provisionnement

## Données et périmètre
Le moteur accepte un triangle annuel carré de 2 à 30 origines. Mack et le bootstrap nécessitent au moins 4 origines. Les cellules observées sont définies par i+j<n en indices Python ; toutes sont requises. Les cellules futures doivent être NA. Les cumuls observés sont strictement positifs dans cette V1 : les zéros ne sont jamais corrigés artificiellement par epsilon.

Les incréments négatifs sont autorisés dans Mack si les cumuls restent positifs. Le bootstrap livré les refuse explicitement ; il ne les supprime ni ne les transforme silencieusement.

Sources :
- Triangle du cours de Nicolas Baradel : https://nicolasbaradel.fr/enseignement/ressources/R/donneesMACK.txt
- Triangles RAA et GenIns de chainladder 0.10.1 : https://github.com/casact/chainladder-python
- Cas réel : CLRD / CAS–NAIC, groupe State Farm Mut Grp, branche ppauto, CumPaidLoss, origines 1988–1997, évaluation 1997-12-31. Un seul groupe et une seule branche sont retenus ; aucune agrégation de groupes et d'entités individuelles n'est faite. Documentation source : https://casact.github.io/raw_package/reference/NAIC.html

Les empreintes des fichiers sont enregistrées dans reports/data_manifest.json. La source du cours est vérifiée contre cette version documentée lors d'une nouvelle récupération. Les jeux de bibliothèque sont figés par la version de package et leurs empreintes. Les fichiers bruts restent sous data/raw, hors Git.

Les unités sont celles de la source, sans conversion en EUR ou USD. Le fichier du cours n'indique pas de calendrier réel ou d'unité monétaire. La conversion technique en objet chainladder utilise des années artificielles 2000+i uniquement pour reproduire la géométrie du triangle ; elles ne sont jamais présentées comme des dates historiques de ce jeu.

GenIns n'est pas un alias exact du cours : en ligne 8, colonne 3, le cours contient 2 864 494 et la bibliothèque 2 864 498. Leurs provisions diffèrent donc légèrement.

## Chain-Ladder
Pour C(i,j), cumul de l'origine i à l'âge j, et k_i son dernier âge connu :

f_j = somme_i C(i,j+1) / somme_i C(i,j), uniquement sur les paires observées.

C_hat(i,n) = C(i,k_i) × produit_{j=k_i}^{n-1} f_j.

R_hat(i) = C_hat(i,n) − C(i,k_i) ; R_hat = somme_i R_hat(i).

Le moteur conserve les observations et la projection dans des tableaux distincts. Les fonctions n'utilisent aucune dimension globale. Le facteur de queue vaut 1, sans estimation ni variance supplémentaire de queue. La charge au dernier âge modélisé est donc supposée ultime ; c'est une hypothèse, pas une observation de l'ultime réel.

Sur un triangle de paiements, R est le restant à payer estimé. Sur un triangle de charges encourues, R est le développement futur de charge ; le reste à payer total requiert en plus les paiements déjà effectués. Sans nature confirmée, l'interface utilise le libellé neutre « développement futur estimé ».

## Mack, alpha=1
Hypothèses : origines indépendantes ; E[C(i,j+1)|passé] = f_j C(i,j) ; Var[C(i,j+1)|passé] = sigma_j² C(i,j). Les facteurs et la structure de variance sont supposés stables entre les origines.

Pour m_j paires observées :

sigma_hat_j² = somme_i (C(i,j+1)−f_hat_j C(i,j))²/C(i,j) / (m_j−1).

Pour la dernière transition avec une seule paire :

sigma_last² = min[(sigma_prev²)²/sigma_before², sigma_prev², sigma_before²].

Si sigma_before² est nulle, le minimum est pris égal à zéro. Cette convention est explicite et testée sur un triangle de développement parfaitement multiplicatif.

Notons S_j = somme_i C(i,j), sur les lignes contribuant à f_j, et U_i l'ultime projeté.

ProcessMSEP_i = U_i² × somme_{j>=k_i} sigma_j² / (f_j² × C_hat(i,j)).

ParamCov(i,k) = U_i U_k × somme_{j>=max(k_i,k_k)} sigma_j² / (f_j² × S_j).

MSEP_i = ProcessMSEP_i + ParamCov(i,i).

MSEP_total = somme_i ProcessMSEP_i + somme_{i,k} ParamCov(i,k).

La covariance interannuelle est incluse au total ; additionner les erreurs standard par année serait incorrect. RMSEP = racine(MSEP). Mack ne définit pas une loi complète : aucun quantile n'est obtenu en traitant automatiquement R ± 1,96 RMSEP comme un intervalle valide.

Référence externe : Development(average='volume', sigma_interpolation='mack') puis MackChainladder dans chainladder. Référence R facultative : est.sigma='Mack', alpha=1, tail=FALSE, mse.method='Mack'. Les résultats RAA publiés avec la variance log-linéaire par défaut ne sont pas directement comparables sans harmoniser cette option.

## Bootstrap ODP : algorithme livré
Ce bootstrap est distinct du bootstrap Mack du cours.

1. Ajuster l'espérance des montants incrémentaux par la structure multiplicative origine × développement compatible avec Chain-Ladder.
2. Calculer les résidus de Pearson et la dispersion ODP : phi = somme (X−mu)²/mu / (N−p), avec p=2n−1.
3. Ajuster les résidus par le levier h : r = (X−mu)/sqrt[mu(1−h)], puis centrer le pool de rééchantillonnage. Les deux observations saturées h=1 n'ont pas de résidu estimable et reçoivent une correction nulle.
4. Rééchantillonner, reconstruire les pseudo-triangles et réestimer leur développement.
5. Ajouter la variance de processus avec l'algorithme Gamma signé de la bibliothèque : pour un futur incrément moyen m, tirer signe(m) × Gamma(forme=abs(m)/phi, échelle=phi).

Lorsque m>0, l'espérance du processus est m et sa variance phi m. Lorsque m<0, la bibliothèque emploie l'extension signée, de variance phi abs(m). Ce dernier cas dépasse le modèle ODP strict à moyenne positive. Le nombre de cellules et de scénarios concernés est affiché et exporté. Aucune troncature n'est appliquée pour cacher ces scénarios.

La graine est explicite (42 par défaut), avec une seconde graine seed+1 pour le processus. La valeur 0 est refusée pour éviter une branche non déterministe de la version utilisée. Les résultats non finis hors origine entièrement développée provoquent une erreur ; aucune simulation invalide n'est supprimée pour produire les quantiles.

### Correction ciblée de bibliothèque
Dans chainladder 0.10.1, _get_hat emploie un numpy.divide avec where sans out. Les observations de levier saturé peuvent donc utiliser de la mémoire non initialisée, ce qu'un test de reproductibilité a effectivement détecté.

StableBootstrapODP remplace uniquement ce calcul du levier par une résolution pondérée et un tableau explicitement initialisé à zéro pour h=1. Les opérations de rééchantillonnage et de processus de la bibliothèque sont conservées. Un test impose les deux corrections nulles et un autre compare deux simulations à graine identique, valeur par valeur. Ce correctif local est versionné et doit être réévalué si chainladder est mis à jour.

Les quantiles sont calculés sur les montants de réserve simulés ; ils décrivent ce modèle et cet horizon. L'erreur Monte-Carlo de la moyenne et quatre Q95 de lots disjoints sont fournis. Ces lots ne sont pas un intervalle de confiance du Q95.

## Validation rétrospective
Trois arrêts de données antérieurs sont reconstruits en masquant des diagonales connues. Tous les facteurs sont réestimés depuis le seul triangle disponible à l'arrêt. La diagonale suivante est comparée aux observations retenues en réserve.

La nouvelle origine est exclue, car ce n'est pas du provisionnement d'origines déjà connues. La plus ancienne origine au-delà de la maturité ajustée est aussi exclue pour ne pas prétendre prédire un facteur de queue non estimé. Le bilan porte sur les incréments futurs des cellules restantes. Un test vérifie qu'une modification des observations masquées ne modifie pas leur propre prédiction.

Cette validation teste le développement à une diagonale, pas l'ultime réel ni un besoin de capital à un an. Trois arrêts sur un seul triangle restent un échantillon limité.

## Limites et extensions
Les tests vérifient les calculs et leur réconciliation ; ils ne démontrent pas que le portefeuille respecte les hypothèses. Une utilisation en compagnie exige une revue des cadences, des segments, de l'inflation, des changements de gestion, des données manquantes et de la queue. Il n'y a ni actualisation, ni inflation modélisée, ni risque de modèle exhaustif, ni SCR calculé.

## Schnieper (livré)

Référence : cours de N. Baradel §5 (modèle, estimateurs, variance) et §6.4.1 (bootstrap), d'après Schnieper (1991).

- **Modèle.** C[i,j+1] = C[i,j] + N[i,j+1] − D[i,j+1], avec E[N|passé] = λⱼEᵢ, Var = σⱼ²Eᵢ, E[D|passé] = δⱼC, Var = τⱼ²C. D > 0 est une baisse de charge. Un triangle C seul ne permet pas d'identifier N et D : le modèle exige N, D et l'exposition E.
- **Estimateurs.** λ̂ⱼ = ΣN/ΣE ; δ̂ⱼ = ΣD/ΣC ; σ̂ⱼ², τ̂ⱼ² avec dénominateurs n−j et n−j−1 ; σ̂ₙ² = τ̂ₙ₋₁² = 0 par convention du cours, non testée. Projection Ĉ[i,j] = λ̂ⱼEᵢ + (1−δ̂ⱼ₋₁)Ĉ[i,j−1].
- **Décomposition.** Vrais IBNR = Σ λ̂ⱼEᵢ futurs ; IBNER = −Σ δ̂ⱼ₋₁Ĉ[i,j−1] futurs ; leur somme est la provision (testé).
- **Variance analytique.** Lemme 5.13 : Var(C[i,j]|F) = σⱼ²Eᵢ + τⱼ₋₁²E(C[i,j−1]) + (1−δⱼ₋₁)²Var(C[i,j−1]), sous Cov(N,D)=0. Processus seul, paramètres supposés connus ; vérifiée contre la forme développée du lemme et contre une simulation gaussienne.
- **Bootstrap.** Résidus de Pearson ajustés des degrés de liberté puis centrés, tirés séparément pour N et D ; reconstruction du passé, réestimation de λ, δ, σ, τ, puis projection stochastique avec plancher à 0 (`pmax` du cours). Les scénarios planchés sont comptés, jamais écartés ; le plancher biaise légèrement la moyenne à la hausse.
- **Validation.** Toutes les valeurs imprimées de l'exemple 5.4 sont reproduites (λ, δ, σ, τ, ultimes, provisions, 283,9 ; Mack 464,2) ainsi que l'exemple 5.6 (7,97). Invariance d'unité (remarque 5.10) testée. La Table 6 du cours n'est pas reproduite : elle se rattache à un jeu ambigu.
- **Limites.** Un seul triangle de 7 années, aucune validation rétrospective, pas de facteur de queue, pas d'inflation. L'écart avec Mack (283,9 contre 464,2) est un risque de modèle.

L'inflation devrait être appliquée aux incréments par année calendaire, avec une base d'indice et des hypothèses explicites ; elle reste une extension.

Sources méthodologiques :
- https://mages.github.io/ChainLadder/articles/ChainLadder.html
- https://chainladder-python.readthedocs.io/main/library/generated/chainladder.BootstrapODPSample.html
- https://chainladder-python.readthedocs.io/main/getting_started/tutorials/stochastic-tutorial.html
- Cours fourni de Nicolas Baradel, p. 25–69.
