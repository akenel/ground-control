#!/usr/bin/env bash
#
# Run Aider against Ollama.com (the hosted cloud API, NOT local ollama).
#
#   ./run-aider-ollama.sh                    # fetch model list, pick one, launch
#   ./run-aider-ollama.sh -l                 # just list what's available
#   ./run-aider-ollama.sh kimi-k3            # skip the menu
#   ./run-aider-ollama.sh kimi-k3 --yes src/ # everything after the model goes to aider
#
# The API key is NOT stored in this file. Provide it via:
#   export OLLAMA_API_KEY=...      (recommended — put it in ~/.zshrc)
#   or write it to ~/.ollama/api-key
# Get one at https://ollama.com/settings/keys

set -euo pipefail

OLLAMA_CLOUD_HOST="${OLLAMA_CLOUD_HOST:-https://ollama.com}"
TAGS_URL="$OLLAMA_CLOUD_HOST/api/tags"

# openai = talk to Ollama.com's OpenAI-compatible /v1 endpoint (default, most reliable)
# native = use litellm's ollama provider against OLLAMA_API_BASE
AIDER_OLLAMA_MODE="${AIDER_OLLAMA_MODE:-openai}"

die() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }
info() { printf '\033[2m%s\033[0m\n' "$*" >&2; }

# ---------------------------------------------------------------- args
LIST_ONLY=0
MODEL_NAME="${MODEL_NAME:-}"
MODEL_EXPLICIT=0
AIDER_ARGS=()

while [ $# -gt 0 ]; do
  case "$1" in
    -l|--list) LIST_ONLY=1; shift ;;
    -m|--model) [ $# -ge 2 ] || die "--model needs a value"; MODEL_NAME="$2"; MODEL_EXPLICIT=1; shift 2 ;;
    -h|--help) sed -n '3,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --) shift; AIDER_ARGS+=("$@"); break ;;
    *)  # bare words are ambiguous (model name vs. a file for aider) — resolved
        # against the real catalogue further down
        AIDER_ARGS+=("$1"); shift ;;
  esac
done
[ -n "$MODEL_NAME" ] && MODEL_EXPLICIT=1

# ---------------------------------------------------------------- deps
command -v curl >/dev/null || die "curl not found"
if [ "$LIST_ONLY" -eq 0 ]; then
  command -v aider >/dev/null || die "aider not found on PATH (pip install aider-install && aider-install)"
fi

# ---------------------------------------------------------------- key
if [ -z "${OLLAMA_API_KEY:-}" ]; then
  for f in "$HOME/.ollama/api-key" "$HOME/.config/ollama/api-key"; do
    if [ -r "$f" ]; then
      OLLAMA_API_KEY="$(tr -d '[:space:]' < "$f")"
      info "key loaded from $f"
      break
    fi
  done
fi
[ -n "${OLLAMA_API_KEY:-}" ] || die "OLLAMA_API_KEY is not set.
  export OLLAMA_API_KEY=...   or   echo '<key>' > ~/.ollama/api-key && chmod 600 ~/.ollama/api-key
  Keys: https://ollama.com/settings/keys"
export OLLAMA_API_KEY

# Stop aider falling back to Claude / OpenAI creds that happen to be in the shell.
unset ANTHROPIC_API_KEY ANTHROPIC_API_BASE OPENAI_API_KEY OPENAI_API_BASE

# ---------------------------------------------------------------- fetch catalogue
info "fetching model list from $TAGS_URL ..."
RAW=""
for attempt in 1 2 3; do
  if RAW="$(curl -fsS --max-time 20 -H "Authorization: Bearer $OLLAMA_API_KEY" "$TAGS_URL")"; then
    break
  fi
  RAW=""
  [ "$attempt" -lt 3 ] && { info "retry $attempt/3 ..."; sleep 2; }
done
[ -n "$RAW" ] || die "could not reach $TAGS_URL — check network / OLLAMA_CLOUD_HOST"

# name<TAB>size<TAB>modified, sorted by name
if command -v jq >/dev/null; then
  ROWS="$(printf '%s' "$RAW" | jq -r '
    (.models // .data // [])[]
    | [ (.name // .model // .id), ((.size // 0)|tostring), ((.modified_at // "")|tostring[0:10]) ]
    | @tsv' | sort -f)"
else
  info "jq not installed — falling back to crude parsing (names only)"
  ROWS="$(printf '%s' "$RAW" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | sed 's/$/\t0\t/' | sort -f)"
fi
[ -n "$ROWS" ] || die "no models returned by $TAGS_URL"

mapfile -t NAMES < <(printf '%s\n' "$ROWS" | cut -f1)

fmt_row() { # name size modified -> pretty line
  awk -F'\t' '{
    s = $2 + 0
    sz = (s > 0) ? sprintf("%.0f GB", s/1e9) : "-"
    printf "%-24s %10s   %s\n", $1, sz, $3
  }' <<<"$1"
}

if [ "$LIST_ONLY" -eq 1 ]; then
  printf '%s\n' "$ROWS" | while IFS= read -r r; do fmt_row "$r"; done
  exit 0
fi

# ---------------------------------------------------------------- pick a model
in_list() { local m="$1" n; for n in "${NAMES[@]}"; do [ "$n" = "$m" ] && return 0; done; return 1; }

if [ "$MODEL_EXPLICIT" -eq 1 ] && ! in_list "$MODEL_NAME"; then
  die "'$MODEL_NAME' is not in the Ollama.com catalogue — run '$0 -l' to see what is"
fi

# No explicit model: a leading bare word that names a real model is the model,
# otherwise every bare word stays an aider argument (file paths, etc).
if [ -z "$MODEL_NAME" ] && [ "${#AIDER_ARGS[@]}" -gt 0 ] && in_list "${AIDER_ARGS[0]}"; then
  MODEL_NAME="${AIDER_ARGS[0]}"
  AIDER_ARGS=("${AIDER_ARGS[@]:1}")
fi

if [ -z "$MODEL_NAME" ]; then
  [ -t 0 ] || die "no model given and no terminal to ask on — pass one: $0 <model>"

  if [ -z "${NO_FZF:-}" ] && command -v fzf >/dev/null; then
    sel="$(printf '%s\n' "$ROWS" | while IFS= read -r r; do fmt_row "$r"; done \
      | fzf --prompt='ollama.com model > ' --height=60% --reverse \
            --header='name                          size   updated')" || true
    [ -n "$sel" ] || die "no model selected"
    MODEL_NAME="${sel%% *}"
  else
    echo >&2
    printf '  %-3s %-24s %10s   %s\n' "#" "MODEL" "SIZE" "UPDATED" >&2
    i=0
    while IFS= read -r r; do
      i=$((i+1))
      printf '  %-3s %s\n' "$i" "$(fmt_row "$r")" >&2
    done <<<"$ROWS"
    echo >&2
    read -r -p "pick a model [1-${#NAMES[@]}]: " choice
    case "$choice" in
      ''|*[!0-9]*) die "not a number: $choice" ;;
    esac
    [ "$choice" -ge 1 ] && [ "$choice" -le "${#NAMES[@]}" ] || die "out of range: $choice"
    MODEL_NAME="${NAMES[$((choice-1))]}"
  fi
fi

# ---------------------------------------------------------------- launch
if [ "$AIDER_OLLAMA_MODE" = "native" ]; then
  export OLLAMA_API_BASE="$OLLAMA_CLOUD_HOST"
  AIDER_MODEL="ollama/$MODEL_NAME"
else
  export OPENAI_API_BASE="$OLLAMA_CLOUD_HOST/v1"
  export OPENAI_API_KEY="$OLLAMA_API_KEY"
  AIDER_MODEL="openai/$MODEL_NAME"
fi

echo
info "host:  $OLLAMA_CLOUD_HOST  (mode: $AIDER_OLLAMA_MODE)"
info "model: $AIDER_MODEL"
echo

exec aider --model "$AIDER_MODEL" "${AIDER_ARGS[@]}"
