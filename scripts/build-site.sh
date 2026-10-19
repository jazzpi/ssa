#!/usr/bin/env bash
# Executes every notebooks/*.py and renders it to _site/<name>.html plus an index.
set -euo pipefail

cd "$(dirname "$0")/.."
out=_site
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

rm -rf "$out"
mkdir -p "$out"

for py in notebooks/*.py; do
  name=$(basename "$py" .py)
  jupytext --to ipynb --set-kernel python3 --execute --run-path "$(dirname "$py")" --output "$work/$name.ipynb" "$py"
  jupyter nbconvert --to html --output-dir "$out" "$work/$name.ipynb"
done

{
  echo '<!doctype html><meta charset="utf-8"><title>SSA notebooks</title>'
  echo '<h1>SSA notebooks</h1><ul>'
  for py in notebooks/*.py; do
    name=$(basename "$py" .py)
    title=$(sed -n 's/^# # \(.*\)/\1/p' "$py" | head -n1)
    echo "<li><a href=\"$name.html\">${title:-$name}</a></li>"
  done
  echo '</ul>'
} > "$out/index.html"
