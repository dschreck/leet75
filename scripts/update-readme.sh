#!/usr/bin/env bash
# Regenerates the solutions table in the root README.md from each problem's README.md.
# Usage: scripts/update-readme.sh [--stdout]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
README="$ROOT/README.md"
BEGIN_MARKER="<!-- BEGIN SOLUTIONS TABLE -->"
END_MARKER="<!-- END SOLUTIONS TABLE -->"

extract() {
  # Emits: order<TAB>title<TAB>difficulty<TAB>category<TAB>leetcode<TAB>dir
  awk -v dir="$1" '
    function cell(line,   v) {
      v = line
      sub(/^[^|]*\|[^|]*\|[[:space:]]*/, "", v)   # drop "| **Key** | "
      sub(/[[:space:]]*\|[[:space:]]*$/, "", v)   # drop trailing "|"
      gsub(/\|/, "\\|", v)                        # escape pipes for markdown
      return v
    }
    title == "" && /^#[[:space:]]/  { title = substr($0, 3); sub(/[[:space:]]+$/, "", title) }
    /^\|[[:space:]]*\*\*Difficulty\*\*/  { difficulty = cell($0) }
    /^\|[[:space:]]*\*\*Category\*\*/    { category   = cell($0) }
    /^\|[[:space:]]*\*\*Plan order\*\*/  { order      = cell($0) }
    /^\|[[:space:]]*\*\*LeetCode\*\*/    { url        = cell($0) }
    END {
      n = (match(order, /^[0-9]+/)) ? substr(order, 1, RLENGTH) + 0 : 9999
      printf "%d\t%s\t%s\t%s\t%s\t%s\n", n, title, difficulty, category, url, dir
    }
  ' "$ROOT/$1/README.md"
}

build_table() {
  echo "| # | Problem | Difficulty | Category | LeetCode |"
  echo "| ---: | --- | --- | --- | --- |"
  for dir in "$ROOT"/[0-9]*_*/; do
    extract "$(basename "$dir")"
  done | sort -t $'\t' -k1,1n -k6,6 | while IFS=$'\t' read -r order title difficulty category url dir; do
    [ "$order" -eq 9999 ] && order="—"
    echo "| $order | [$title]($dir/README.md) | $difficulty | $category | [Solve]($url) |"
  done
}

TABLE_FILE="$(mktemp)"
trap 'rm -f "$TABLE_FILE" "$README.tmp"' EXIT
build_table > "$TABLE_FILE"

if [ "${1:-}" = "--stdout" ]; then
  cat "$TABLE_FILE"
  exit 0
fi

if ! grep -qF "$BEGIN_MARKER" "$README"; then
  printf '\n%s\n%s\n' "$BEGIN_MARKER" "$END_MARKER" >> "$README"
fi

awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" -v tablefile="$TABLE_FILE" '
  index($0, begin) {
    print; print ""
    while ((getline line < tablefile) > 0) print line
    close(tablefile)
    print ""
    skip = 1
    next
  }
  index($0, end) { skip = 0 }
  !skip          { print }
' "$README" > "$README.tmp"
mv "$README.tmp" "$README"

echo "Updated $README ($(($(wc -l < "$TABLE_FILE") - 2)) problems)"
