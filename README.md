# 🏔️ Gestion de stockage

**Un gestionnaire de fichiers et d'espace disque simple, visuel et prudent**, créé pour Linux (Ubuntu et distributions compatibles Debian) avec une préversion Windows en développement.

Il permet d'explorer les dossiers, renommer/copier/déplacer des fichiers, consulter l'espace disponible, rechercher les fichiers volumineux et repérer les doublons **sans les supprimer automatiquement**. La page d'accueil conserve son paysage de montagne.

## ⬇️ Installer le logiciel

> **Téléchargez depuis ce dépôt officiel**, pas depuis des sites de téléchargement inconnus : [Toutes les versions GitHub](https://github.com/eliott39pro39-png/gestion-des-stockage/releases).

### 🐧 Ubuntu, Linux Mint, Zorin OS, Pop!_OS, Debian

1. Ouvrez la page **[Dernière version officielle](https://github.com/eliott39pro39-png/gestion-des-stockage/releases/latest)**.
2. Dépliez **Assets** si nécessaire.
3. Cliquez sur le fichier **`gestion-stockage-VERSION-all.deb`** (où VERSION est le numéro affiché). **Ne choisissez pas « Source code »** : c'est le code pour les développeurs, pas le programme à installer.
4. Ouvrez le fichier `.deb` téléchargé avec le gestionnaire de logiciels de votre distribution, puis choisissez **Installer / Mettre à niveau**. Le mot de passe de votre session peut être demandé.
5. Lancez **Gestion de stockage** depuis le menu des applications.

Si le gestionnaire de logiciels affiche « Déjà installé » mais que la version n'est pas la bonne, ouvrez un terminal **dans le dossier contenant le fichier .deb**, puis exécutez :

```bash
sudo apt install ./gestion-stockage-*-all.deb
```

La commande fonctionne si le dossier contient uniquement le paquet souhaité correspondant à ce motif. Pour connaître la version réellement installée :

```bash
dpkg-query -W -f='${Version}\n' gestion-stockage
```

**Attention :** le paquet `.deb` n'est pas destiné à Fedora, Arch, openSUSE ou toutes les distributions Linux. Pour ces systèmes, il faudra une distribution Flatpak ou un paquet natif spécifique ; ce n'est pas encore proposé officiellement.

### 🪟 Windows 10 / 11 — préversion expérimentale

La version Windows est encore **expérimentale** : elle est compilée automatiquement, mais son interface n'a pas été entièrement vérifiée sur un véritable ordinateur Windows. Elle ne possède pas encore d'installateur `.exe` traditionnel.

1. Rendez-vous dans [GitHub Actions](https://github.com/eliott39pro39-png/gestion-des-stockage/actions/workflows/build-windows.yml).
2. Ouvrez la **dernière exécution réussie** de « Build Windows preview » (coche verte).
3. En bas de la page, dans **Artifacts**, téléchargez **GestionStockage-Windows-…-preview**. GitHub peut demander une connexion pour télécharger les artifacts.
4. Décompressez l'archive ZIP, puis ouvrez le dossier **GestionStockage-Windows** et lancez **GestionStockage-Windows.exe**.
5. Gardez **tout le dossier extrait** : l'exécutable utilise les fichiers situés à côté de lui. Si Windows SmartScreen affiche un avertissement, n'exécutez le programme que si vous avez vérifié sa provenance et lui faites confiance.

**Ne téléchargez pas « Source code (zip) » pour installer Windows.** Il ne contient pas d'installateur Windows prêt à l'emploi.

### ❓ Questions fréquentes

**Le logiciel dit « Déjà installé ».** Vérifiez la version avec `dpkg-query` ci-dessus. Si elle est ancienne, installez explicitement le nouveau `.deb`.

**Comment utiliser les fichiers ?** Un **clic** sélectionne un fichier pour le renommer, copier ou déplacer. Un **double-clic** l'ouvre. Les boutons d'action apparaissent après la sélection.

**Le bouton de mise à jour ne marche pas sur une ancienne version.** Téléchargez et installez manuellement le dernier `.deb` officiel. La version **27.5.1** corrige un défaut de vérification du paquet téléchargé.

**Puis-je effacer tous les doublons ?** Le radar des doublons fonctionne en lecture seule jusqu'à votre sélection. Les fichiers ne sont jamais supprimés automatiquement et l'application empêche de sélectionner toutes les copies d'un groupe.

**Mes fichiers sont-ils envoyés sur Internet ?** Les fonctions locales de gestion de fichiers n'envoient pas le contenu des fichiers vers GitHub. La recherche de mises à jour interroge l'API GitHub pour connaître la dernière version.

## ✨ Fonctionnalités

- Explorateur avec liste ou grille, tri, recherche et filtres
- Actions sur les fichiers avec confirmation pour les opérations destructrices
- Tableau de bord de l'espace utilisé et disponible
- Détective de stockage : analyse des fichiers volumineux
- Radar des doublons : comparaison par contenu SHA-256
- Favoris, téléchargements, personnalisation et anciennes versions

## 🛡️ Sécurité et limites

- Les analyses de stockage et de doublons sont **en lecture seule**.
- Vérifiez toujours les chemins avant de déplacer ou supprimer un fichier.
- Les copies et déplacements volumineux sont exécutés en arrière-plan ; ne fermez pas l'application avant la fin.
- Les versions Windows restent des préversions, pas des logiciels certifiés pour tous les PC.
- Les mises à jour Linux sont téléchargées avec votre accord ; une installation peut nécessiter un mot de passe administrateur.
- **Aucun dépôt APT officiel ni mise à jour automatique système n'est fourni pour le moment.**

## 🚀 Trois idées pour les prochaines grandes versions

1. **Rangement intelligent, mais sous contrôle** : l'application propose où classer les fichiers (Documents, Images, Vidéos, Archives), montre un aperçu précis de chaque déplacement et n'agit qu'après confirmation. Possibilité d'annuler les déplacements.
2. **Carte du disque interactive** : une vue graphique des dossiers qui occupent le plus de place, avec zoom, filtres et accès direct aux fichiers volumineux. L'analyse reste locale et en lecture seule.
3. **Coffre de sauvegarde et restauration** : comparer deux dossiers ou disques, détecter ce qui a changé, préparer une copie de sauvegarde, puis restaurer des fichiers individuellement après vérification.

Ces trois fonctionnalités sont des **projets**, pas des fonctions déjà disponibles. La priorité est la sécurité des fichiers et les tests sur Linux et Windows.

## 🛠️ Pour contribuer

Sources principales : `app.py` (Python / GTK4), `windows/app_windows.py` (adaptation Windows), `packaging/` (paquet Debian), `tests/` (tests automatisés).

Pour signaler un problème ou proposer une idée : [Issues](https://github.com/eliott39pro39-png/gestion-des-stockage/issues). Précisez votre système, votre version et les étapes pour reproduire le problème.

Les builds sont produits par GitHub Actions ; une compilation réussie ne remplace pas les tests manuels sur Linux et Windows.
