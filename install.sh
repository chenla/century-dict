#!/bin/bash
# Install the Century Dictionary into the local dictd, beside GCIDE.
# Debian's dictdconfig auto-discovers any <name>.dict.dz + <name>.index pair in
# /usr/share/dictd, so a dictionary package is just those two files.
#   sudo bash ~/proj/century/install.sh
set -e
[ "$EUID" -eq 0 ] || { echo "needs root: sudo bash $0" >&2; exit 1; }
cd "$(dirname "$0")"
for f in century.dict.dz century.index; do
  [ -s "$f" ] || { echo "missing $f -- run ./build.py first" >&2; exit 1; }
done
install -m 644 century.dict.dz century.index /usr/share/dictd/
dictdconfig --write
systemctl restart dictd
sleep 1
echo "== active: $(systemctl is-active dictd)"
echo "== databases:"; dict -h localhost -D 2>&1 | sed 's/^/   /'
echo "== Century on 'sublime':"
dict -h localhost -d century sublime 2>&1 | sed -n '4,7p' | sed 's/^/   /'
