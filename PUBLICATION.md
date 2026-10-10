# Publication d'une nouvelle version

## Prérequis

Avant toute publication, ajouter et vérifier à la racine du dépôt :
- `app.py` : code source de l'application
- `mountain-bg.png` : image utilisée par l'interface
- `versions/` : anciennes versions conservées par l'application
- tout autre fichier effectivement nécessaire à l'exécution

Ne pas publier de jetons d'accès, clés privées ou données personnelles.

## Construction

Depuis un système Debian/Ubuntu avec `dpkg-deb` :

```bash
python3 -m py_compile app.py
bash packaging/build-deb.sh 27.2.1
```

Le paquet sera généré dans `dist/`. Tester son installation et les principales fonctionnalités sur une machine Linux de test avant de publier une release.

## Publication

Après validation, créer un tag de version au format `vX.Y.Z`. Le workflow GitHub Actions construira un paquet et tentera de créer une GitHub Release correspondante.

**Attention :** le dépôt n'est pas encore une source de mises à jour APT. Une GitHub Release n'installe pas automatiquement les mises à jour sur les machines des utilisateurs.

## Mises à jour pour les utilisateurs

- À court terme : proposer les téléchargements depuis GitHub Releases.
- Pour Ubuntu/Debian : publier un dépôt APT signé et documenter son installation.
- Pour d'autres distributions : envisager un Flatpak et sa distribution.

La publication des versions doit être déclenchée après validation de leur fonctionnement.
