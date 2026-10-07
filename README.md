# PerfComparator Web

PCWEB est la façade Web locale de PerfComparator. Elle sert une interface HTML
et communique avec PerfComparator Engine (PCE) par son API HTTP locale. Le
paquet Python et sa commande s’appellent `perfcomparatorweb`.

[Tous les tags](https://github.com/frchalaoux/perfcomparator-web/tags)

Le dépôt public `perfcomparator-web` héberge le composant PCWEB indépendamment
de PCE. Le premier socle expose une page de diagnostic de la connexion à PCE ;
les parcours de campagne et de rapport seront ajoutés dans les phases suivantes.

Dans l’installation groupée, démarrez et arrêtez les deux services avec
`perfcomparator web start` et `perfcomparator web stop`. Pour le développement,
`perfcomparatorweb start|stop|status` contrôle PCWEB seul ; PCE doit déjà
fonctionner et son état privé doit être disponible dans le répertoire d’état
utilisateur.
