#!/bin/bash
# Fetch the Century Dictionary markdown extraction (42 MB, 187,438 headwords).
# Public domain source (1889-91); the extraction is hupong/century-dictionary.
set -e
cd "$(dirname "$0")"
mkdir -p data
if [ -s data/century.md ]; then echo "  have data/century.md"; else
  curl -fL --retry 3 -o data/century.md \
    https://raw.githubusercontent.com/hupong/century-dictionary/master/century.md
fi
ls -la data/century.md
echo "ok -- now run ./build.py data/century.md"
