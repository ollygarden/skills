#!/usr/bin/env bash
# Keep the skill registration points in sync with skills/ on disk.
#
# A skill is only "registered" when it appears in all of these, and every one of
# them has drifted before:
#   1. skills/<name>/SKILL.md            — the skill itself
#   2. .claude-plugin/marketplace.json   — the Claude Code plugin entry
#   3. README.md "Available Skills"      — the table contributors read
#   4. README.md layout tree             — the fenced `skills/` listing
#
# Checks run in BOTH directions: a skill with no entry, and an entry naming a
# skill that does not exist. The marketplace `source` path is checked against
# the entry name too, since a copy-pasted entry that points at the wrong
# directory installs the wrong skill.
#
# Duplicates are reported rather than folded away. A list deduplicated before
# comparison passes with two identical entries in it, which is exactly what a
# copy-paste registration produces.
#
# Usage: bin/check-skill-inventory.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

README="README.md"
MARKETPLACE=".claude-plugin/marketplace.json"

failures=0
fail() {
  echo "FAIL: $*" >&2
  failures=$((failures + 1))
}

contains() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    [ "$item" = "$needle" ] && return 0
  done
  return 1
}

for f in "$README" "$MARKETPLACE"; do
  [ -f "$f" ] || {
    echo "FAIL: $f not found; run from anywhere, but the repository must be intact" >&2
    exit 1
  }
done

command -v jq >/dev/null 2>&1 || {
  echo "FAIL: jq not found on PATH; it is required to read $MARKETPLACE" >&2
  exit 1
}

# read_into <array-name> — portable mapfile; macOS ships bash 3.2, which has none.
read_into() {
  local __name="$1"
  local __line
  eval "$__name=()"
  while IFS= read -r __line; do
    [ -n "$__line" ] || continue
    eval "$__name+=(\"\$__line\")"
  done
}

read_into SKILLS < <(find skills -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)
[ "${#SKILLS[@]}" -gt 0 ] || {
  echo "FAIL: no skills found under skills/" >&2
  exit 1
}

# report_duplicates <label> <name...> — a list is deduplicated only after any
# repeat in it has been reported, so a copy-pasted entry cannot pass by merging
# with the one it was copied from.
report_duplicates() {
  local label="$1"
  shift
  local dup
  while IFS= read -r dup; do
    [ -n "$dup" ] || continue
    fail "$label lists '$dup' more than once"
  done < <(printf '%s\n' "$@" | sort | uniq -d)
}

# Table rows look like: | [`skill-name`](skills/skill-name/) | description |
# Both the label and the link target are required, so a row whose link points at
# a different skill is reported rather than silently accepted, and prose
# elsewhere in the README is not mistaken for a skill row.
read_into README_ROWS < <(
  grep -oE '^\| \[`[a-z0-9-]+`\]\(skills/[a-z0-9-]+/\)' "$README" |
    sed -E 's/^\| \[`([a-z0-9-]+)`\]\(skills\/([a-z0-9-]+)\/\)/\1 \2/' |
    awk '$1 == $2 { print $1 } $1 != $2 { print "MISMATCH:" $1 ":" $2 }'
)

# Layout tree entries look like: ├── skill-name/   (or └── for the last one)
#
# Scoped to the block introduced by the `skills/` root line and ended by the
# closing fence, not searched across the whole README. A repository-structure
# tree listing `bin/` or `docs/` is a plausible future addition, and a
# document-wide match would read those as skills that do not exist on disk —
# failing the build for a correct README.
read_into README_TREE < <(
  awk '
    $0 == "skills/" { inblock = 1; next }
    inblock && /^```/ { inblock = 0 }
    inblock && /^(├──|└──) [a-z0-9-]+\/$/ { print }
  ' "$README" |
    sed -E 's/^(├──|└──) ([a-z0-9-]+)\/$/\2/'
)

read_into MARKETPLACE_ENTRIES < <(jq -r '.plugins[].name' "$MARKETPLACE")

report_duplicates "the $README 'Available Skills' table" ${README_ROWS[@]+"${README_ROWS[@]}"}
report_duplicates "the $README layout tree" ${README_TREE[@]+"${README_TREE[@]}"}
report_duplicates "$MARKETPLACE" ${MARKETPLACE_ENTRIES[@]+"${MARKETPLACE_ENTRIES[@]}"}

for row in "${README_ROWS[@]}"; do
  case "$row" in
    MISMATCH:*)
      label="${row#MISMATCH:}"
      fail "$README has a row labelled '${label%%:*}' linking to 'skills/${label##*:}/'; the label and the link must name the same skill"
      ;;
  esac
done

for skill in "${SKILLS[@]}"; do
  [ -f "skills/$skill/SKILL.md" ] || fail "skills/$skill has no SKILL.md"

  contains "$skill" "${README_ROWS[@]}" ||
    fail "$skill has no row in the $README 'Available Skills' table"

  contains "$skill" "${README_TREE[@]}" ||
    fail "$skill is missing from the $README layout tree"

  contains "$skill" "${MARKETPLACE_ENTRIES[@]}" ||
    fail "$skill has no entry in $MARKETPLACE"
done

for name in "${README_ROWS[@]}"; do
  case "$name" in MISMATCH:*) continue ;; esac
  contains "$name" "${SKILLS[@]}" ||
    fail "$README lists '$name', which is not a directory under skills/"
done

for name in "${README_TREE[@]}"; do
  contains "$name" "${SKILLS[@]}" ||
    fail "the $README layout tree lists '$name', which is not a directory under skills/"
done

for name in "${MARKETPLACE_ENTRIES[@]}"; do
  contains "$name" "${SKILLS[@]}" ||
    fail "$MARKETPLACE lists '$name', which is not a directory under skills/"
done

# Marketplace source paths must point at the matching directory. This loop runs
# over every entry, including one whose name is not a skill on disk: an entry
# that is both unknown and misdirected reports both problems. Do not narrow it to
# known skills — that would make the source check depend on the unknown-entry
# check firing, and a hole opens the moment either is relaxed.
while IFS=$'\t' read -r name source; do
  expected="./skills/$name"
  [ "$source" = "$expected" ] ||
    fail "$MARKETPLACE entry '$name' has source '$source', expected '$expected'"
done < <(jq -r '.plugins[] | [.name, .source] | @tsv' "$MARKETPLACE")

if [ "$failures" -gt 0 ]; then
  echo "" >&2
  echo "$failures inventory problem(s). See CONTRIBUTING.md, 'Adding or changing a skill'." >&2
  exit 1
fi

echo "OK: ${#SKILLS[@]} skills; README table, README layout tree, and marketplace are in sync"
