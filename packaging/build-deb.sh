#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:?Usage: bash packaging/build-deb.sh VERSION}"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?$ ]] || { echo "Invalid version" >&2; exit 1; }
test -f app.py || { echo "Missing app.py: publish the verified application sources first" >&2; exit 1; }
test -f mountain-bg.png || { echo "Missing mountain-bg.png" >&2; exit 1; }
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
pkg="$work/pkg"
mkdir -p "$pkg/DEBIAN" "$pkg/usr/share/gestion-stockage" "$pkg/usr/bin" "$pkg/usr/share/applications" "$pkg/usr/share/icons/hicolor/scalable/apps"
cp app.py smart_tools.py mountain-bg.png "$pkg/usr/share/gestion-stockage/"
cp packaging/gestion-stockage.svg "$pkg/usr/share/icons/hicolor/scalable/apps/gestion-stockage.svg"
if [[ -d versions ]]; then cp -R versions "$pkg/usr/share/gestion-stockage/"; fi
if [[ -f logo.png ]]; then cp logo.png "$pkg/usr/share/gestion-stockage/"; fi
cat > "$pkg/DEBIAN/control" <<EOF
Package: gestion-stockage
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-4.0
Maintainer: Gestion de stockage <noreply@github.com>
Description: Gestionnaire de stockage GTK4 pour Linux
EOF
cat > "$pkg/usr/bin/gestion-stockage" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 /usr/share/gestion-stockage/app.py "$@"
EOF
chmod 755 "$pkg/usr/bin/gestion-stockage"
cat > "$pkg/usr/share/applications/gestion-stockage.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Gestion de stockage
Exec=gestion-stockage
Icon=gestion-stockage
StartupWMClass=io.github.gestionstockage
Terminal=false
Categories=Utility;FileTools;
EOF
mkdir -p dist
dpkg-deb --build --root-owner-group "$pkg" "dist/gestion-stockage-$VERSION-all.deb"
dpkg-deb --info "dist/gestion-stockage-$VERSION-all.deb"
