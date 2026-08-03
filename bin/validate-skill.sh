#!/usr/bin/env bash
# Validate the skills in this repository against the Agent Skills spec plus our
# house rules.
#
# Spec conformance is delegated to `skills-ref`, the reference validator from
# the Agent Skills project. It parses the frontmatter with a YAML parser
# (strictyaml) rather than by pattern-matching lines, so it catches what a
# hand-rolled grep cannot: an unquoted `description:` containing a bare `: `
# breaks the document, and a line-based check happily reports a plausible
# character count for frontmatter that no spec client can load at all.
#
# Delegated to skills-ref:
#   - the frontmatter is parseable YAML
#   - `name` present, lowercase, <= 64 chars, letters/digits/hyphens (Unicode
#     letters included), no leading, trailing, or doubled hyphen, and equal to
#     the directory name
#   - `description` present and <= 1024 chars
#   - `compatibility` <= 500 chars
#   - no frontmatter keys outside the spec's allowed set
#
# Checked here:
#   - SKILL.md exists. Done locally so a missing file reports as itself rather
#     than as a spec violation. Note this is stricter than skills-ref, which
#     also accepts a lowercase `skill.md`; CONTRIBUTING.md requires `SKILL.md`.
#   - SKILL.md is under 500 lines. The number is humus's, and the reason travels
#     with it: a SKILL.md is loaded in full whenever the skill triggers, so every
#     line is context an agent pays for on every activation. Detail that does not
#     have to be in the agent's head at trigger time belongs in `references/`,
#     which is read on demand. A skill approaching the cap is usually two skills,
#     or one skill with a reference it has not extracted yet — treat the failure
#     as that signal rather than as a number to raise.
#   - the `name:` carries the `ollygarden-` prefix this repository claims in the
#     global skill namespace. skills-ref only checks name/directory agreement,
#     so the prefix rule needs its own check.
#
# The prefix rule has no exemption list, deliberately. Every skill here carries
# the prefix today and the repository claims it as an invariant in README.md and
# CONTRIBUTING.md, so a list would be an empty mechanism that still has to be
# kept from rotting. (humus needs one because its `hub` skills are invoked by
# bare name.) If this repository ever ships a skill that must not carry the
# prefix, editing this script should be the deliberate, reviewed act that allows
# it — at which point add the same rot checks humus applies to its waiver list:
# an entry for a skill that no longer exists, or one that no longer needs the
# waiver, is itself a failure.
#
# Registration drift — README, marketplace, layout tree — is a separate concern;
# see bin/check-skill-inventory.sh.
#
# Usage: bin/validate-skill.sh [skill-directory ...]
#        With no arguments, validates every skill under skills/.
#
# Exits 0 when every target passes, 1 on any failure.
set -euo pipefail

# Resolve arguments against the caller's directory BEFORE cd'ing to the
# repository root, so a relative path means what the caller typed.
REQUESTED=()
for arg in "$@"; do
  case "$arg" in
    /*) REQUESTED+=("${arg%/}") ;;
    *) REQUESTED+=("${PWD}/${arg%/}") ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v skills-ref >/dev/null 2>&1; then
  echo "FAIL: skills-ref not found on PATH." >&2
  echo "" >&2
  echo "Install the pinned revision:" >&2
  echo "" >&2
  echo "  uv tool install \"\$(cat bin/skills-ref.requirement)\"" >&2
  exit 1
fi

failures=0
fail() {
  echo "FAIL: $*" >&2
  failures=$((failures + 1))
}

if [ "${#REQUESTED[@]}" -gt 0 ]; then
  TARGETS=("${REQUESTED[@]}")
else
  TARGETS=()
  while IFS= read -r dir; do
    TARGETS+=("$dir")
  done < <(find skills -mindepth 1 -maxdepth 1 -type d | sort)
  [ "${#TARGETS[@]}" -gt 0 ] || {
    echo "FAIL: no skills found under skills/" >&2
    exit 1
  }
fi

for target in "${TARGETS[@]}"; do
  # Canonicalize first: stripping the repository prefix does not remove `.` or
  # `..` segments, so `skills/./foo` would validate the right file yet report
  # under a path that does not exist.
  if [ -d "$target" ]; then
    target="$(cd "$target" && pwd -P)"
  fi

  # Present paths relative to the repository root where possible, so output does
  # not depend on how the caller spelled the argument.
  SKILL_DIR="${target#"$REPO_ROOT"/}"
  SKILL_NAME="$(basename "$SKILL_DIR")"
  SKILL_FILE="${SKILL_DIR}/SKILL.md"

  if [ ! -f "$SKILL_FILE" ]; then
    fail "$SKILL_FILE not found"
    continue
  fi

  ok=true

  # House rule: SKILL.md must be *under* 500 lines.
  # Count logical lines, not newline terminators: `wc -l` reports 499 for a
  # 500-line file that lacks a trailing newline, which would slip past the cap.
  LINE_COUNT="$(awk 'END { print NR }' "$SKILL_FILE")"
  if [ "$LINE_COUNT" -ge 500 ]; then
    fail "$SKILL_FILE is $LINE_COUNT lines, must be under 500"
    ok=false
  fi

  # House rule: the ollygarden- namespace prefix. Checked on the directory name,
  # which skills-ref has already tied to the frontmatter `name:`.
  case "$SKILL_NAME" in
    ollygarden-?*) ;;
    *)
      fail "$SKILL_DIR does not carry the required 'ollygarden-' name prefix"
      ok=false
      ;;
  esac

  # Spec conformance. skills-ref exits 1 for validation failures, so anything
  # higher is a crash and must not be reported as a spec violation.
  set +e
  SPEC_OUTPUT="$(skills-ref validate "$SKILL_DIR" 2>&1)"
  SPEC_STATUS=$?
  set -e

  if [ "$SPEC_STATUS" -gt 1 ]; then
    fail "skills-ref crashed on $SKILL_DIR (exit $SPEC_STATUS):
$SPEC_OUTPUT"
  elif [ "$SPEC_STATUS" -ne 0 ]; then
    fail "$SKILL_DIR does not conform to the Agent Skills spec:
$SPEC_OUTPUT"
  elif [ "$ok" = true ]; then
    echo "OK: $SKILL_DIR ($LINE_COUNT lines)"
  fi
done

if [ "$failures" -gt 0 ]; then
  echo "" >&2
  echo "$failures validation problem(s)." >&2
  exit 1
fi

echo "OK: ${#TARGETS[@]} skill(s) validated"
