# Gestion de stockage

Application de bureau Linux en Python et GTK4 pour explorer, organiser et nettoyer ses fichiers.

## État du projet

- Version installable connue : **27.2.1** (paquet Debian `gestion-stockage`, version du paquet `27.2-2`).
- La publication du code source et des paquets officiels sur ce dépôt est en préparation.
- **Aucune mise à jour automatique n'est encore activée** pour les installations existantes.

## Fonctionnalités

Explorateur de fichiers, corbeille, nettoyage, fichiers inutiles, téléchargements, favoris, raccourcis et historique des anciennes versions.

## Distribution et mises à jour prévues

1. Publier des versions vérifiées dans [GitHub Releases](../../releases).
2. Ajouter une vérification facultative des nouvelles versions dans l'application, avec confirmation de l'utilisateur avant toute installation.
3. Préparer un dépôt APT signé pour les distributions compatibles Debian/Ubuntu.
4. Étudier la distribution Flatpak pour les autres distributions Linux.

> Important : publier un fichier `.deb` sur GitHub ne suffit pas à fournir des mises à jour automatiques via APT. Les utilisateurs devront installer/configurer une source de mises à jour de confiance.

## Sécurité

Ne pas exécuter de commandes téléchargées depuis Internet sans vérification. Les futures versions et métadonnées de mises à jour devront être publiées via HTTPS et accompagnées de mécanismes de vérification adaptés.

## Développement

Les sources de la version 27.2.1 doivent encore être ajoutées et vérifiées avant toute nouvelle publication.