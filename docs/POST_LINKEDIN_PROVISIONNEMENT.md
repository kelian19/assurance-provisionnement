# Brouillon LinkedIn — à relire avant publication

Comment vérifier un calcul de provisionnement avant de construire son tableau de bord ?

J’ai commencé par reproduire un exemple du cours de mathématiques de l’assurance dommages de Nicolas Baradel : projection d’un triangle cumulé par Chain-Ladder, calcul des ultimes et différence avec la dernière diagonale observée.

Le recalcul indépendant en Python donne une provision totale de 18 680 847,77 unités, conforme aux 18 680 848 arrondis du support.

Cette étape a aussi révélé un point concret dans le script pédagogique fourni : le triangle projeté est calculé, mais les provisions utilisent ensuite le triangle initial. La séparation entre données observées et projections est donc essentielle.

La suite du projet portera sur l’erreur de prédiction de Mack, le bootstrap et les diagnostics. Ces résultats ne sont pas encore validés ; je ne les présente pas comme acquis.

Ce premier exemple vérifie un calcul déterministe sur un triangle pédagogique. Il ne démontre pas encore la performance sur un portefeuille réel.

Code et plan : https://github.com/kelian19/assurance-provisionnement

#Actuariat #Provisionnement #Assurance #Python
