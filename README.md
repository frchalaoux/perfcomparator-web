# PerfComparator Web

PCWEB est la façade Web locale de PerfComparator. Elle sert une interface HTML
et communique avec PerfComparator Engine (PCE) par son API HTTP locale. Le
paquet Python et sa commande s’appellent `perfcomparatorweb`.

[Tous les tags](https://github.com/frchalaoux/perfcomparator-web/tags)

Le dépôt public `perfcomparator-web` héberge le composant PCWEB indépendamment
de PCE. PCWEB permet de consulter le catalogue et les rapports, puis de préparer
une campagne : avant de la lancer, l’interface interroge PCE pour mesurer les
conditions de la machine et affiche ses avertissements. Après confirmation,
l’interface suit la progression en direct et donne accès au rapport final.

Dans l’installation groupée, démarrez et arrêtez les deux services avec
`perfcomparator start` et `perfcomparator stop`. Pour gérer PCWEB seul, utilisez
`perfcomparatorweb start|stop|status` ; PCE doit déjà fonctionner et son état
privé doit être disponible dans le répertoire d’état utilisateur. La commande
historique `perfcomparator web start` démarre les deux services ; les commandes
`perfcomparator web stop` et `perfcomparator web status` gèrent PCWEB seul.
