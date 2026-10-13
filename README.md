# PerfComparator Web

**PCWEB est l’interface Web locale de PerfComparator.** Elle s’ouvre dans le
navigateur et communique avec PerfComparator Engine (PCE) par son API HTTP
locale. Elle ne requiert ni compte ni serveur distant.

## Version et disponibilité

Le paquet Python s’appelle `perfcomparatorweb`. La préparation locale vise la
version stable `0.1.1`, qui n’est pas encore publiée et n’est donc pas encore
installable depuis une release. La dernière version embarquée dans les
installateurs de l’application complète est `0.1.1.dev0` avec PCE `v0.5.1`.
La [liste de tous les tags](https://github.com/frchalaoux/perfcomparator-web/tags)
permet de retrouver les versions effectivement taguées. Les installateurs de
l’application complète sont construits et publiés depuis le dépôt
[PerfComparator](https://github.com/frchalaoux/perfcomparator) après les essais
sur les systèmes cibles.

## Fonctionnalités

L’interface comporte les pages **Machine**, **Benchmarks**, **Nouvelle
campagne**, **Rapports** et **Comparer**. Elle permet de corriger les
propriétés de modèle de la machine, de sélectionner tous les benchmarks ou des
groupes particuliers, de vérifier les conditions de mesure avant confirmation,
puis de suivre une campagne jusqu’au rapport final.

La page **Rapports** affiche l’historique par lots de 20. Dans **Comparer**, on
peut rechercher parmi tous les rapports et conserver une sélection entre les
lots, choisir une référence, puis exporter la comparaison en HTML détaillé ou
l’imprimer en PDF.

## Démarrer PCWEB séparément

Dans une installation où PCE est déjà démarré :

```sh
perfcomparatorweb start
perfcomparatorweb status
perfcomparatorweb stop
```

La commande `perfcomparatorweb start` échoue si PCE n’est pas disponible. Dans
l’installation groupée, utilisez `perfcomparator start` et
`perfcomparator stop` pour démarrer ou arrêter les deux services ensemble.
PCWEB sert normalement l’interface sur une adresse locale et PCE écoute sur
une autre adresse locale.

## Développement

PCWEB reste dans son dépôt et son paquet Python propres. Ses tests sont lancés
avec `uv run pytest` ; les installateurs utilisateur sont construits depuis le
dépôt PCE afin de fixer et vérifier ensemble les commits PCE et PCWEB inclus.
