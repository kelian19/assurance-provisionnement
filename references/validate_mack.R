# Référence R facultative, non exécutée si Rscript ou ChainLadder est absent.
# Depuis la racine du dépôt : Rscript references/validate_mack.R
if (!requireNamespace("ChainLadder", quietly = TRUE)) {
  stop("Installer ChainLadder avant cette validation indépendante.")
}
C <- as.matrix(read.table("data/raw/donneesMACK.txt", sep = "&", header = FALSE,
                          fill = TRUE, colClasses = "numeric"))
triangle <- ChainLadder::as.triangle(C)
fit <- ChainLadder::MackChainLadder(triangle, alpha = 1,
                                 est.sigma = "Mack", tail = FALSE,
                                 mse.method = "Mack")
reserve <- sum(fit$IBNR)
stopifnot(abs(reserve - 18680847.767812435) < 1e-6)
print(summary(fit))
cat("Version ChainLadder :", as.character(utils::packageVersion("ChainLadder")), "\n")
# Le résultat RAA publié avec la variance log-linéaire par défaut ne doit pas être
# comparé à notre approximation finale de Mack sans harmoniser les options.
