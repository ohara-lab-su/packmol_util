#!/usr/bin/env bash
set -euo pipefail

DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$DOCS_DIR/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"

rm -rf "$DOCS_DIR/_build"
for lang in en ja; do
  rm -rf "$DOCS_DIR/$lang/api"
  mkdir -p "$DOCS_DIR/$lang/api"
  sphinx-apidoc --force --module-first -o "$DOCS_DIR/$lang/api" "$ROOT_DIR/src/packmol_util"
  sphinx-build -b html -D language="$lang" -c "$DOCS_DIR" "$DOCS_DIR/$lang" "$DOCS_DIR/_build/html/$lang"
done

# English is also the root site, built from the SAME English source tree.
sphinx-build -b html -D language=en -c "$DOCS_DIR" "$DOCS_DIR/en" "$DOCS_DIR/_build/html"
touch "$DOCS_DIR/_build/html/.nojekyll"
