# Brouillon LinkedIn — non publié

J’ai construit un outil de provisionnement en Python, avec une interface Streamlit pour passer du triangle à une estimation expliquée.

La première étape a été de reproduire le montant du cours : 18 680 847,77 unités de développement futur estimé. L’erreur de prédiction de Mack vaut 2 447 093,03 unités, soit environ 13,1 % de cette estimation.

Le moteur a ensuite été comparé à une bibliothèque actuarielle indépendante sur le triangle du cours, RAA, GenIns et un périmètre CAS/NAIC.

Pour explorer l’incertitude, j’ai ajouté un bootstrap ODP avec risque de processus. Sur 5 000 scénarios à graine fixée, le quantile à 95 % vaut 24,138,111.42 unités sur le triangle du cours. Ce résultat dépend des hypothèses du bootstrap, dont une extension Gamma signée explicitement documentée ; ce n’est pas un quantile Mack ni un SCR à un an.

Les résultats de validation rétrospective restent visibles même lorsqu’ils sont défavorables. L’outil distingue calcul vérifié et hypothèses à valider sur le portefeuille.

Code, méthodes, résultats et guide local : https://github.com/kelian19/assurance-provisionnement

#Actuariat #Provisionnement #Python #Assurance
