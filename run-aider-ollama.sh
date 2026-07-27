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
KEY_FILE="$HOME/.ollama/api-key"

# Read a secret without echoing it, showing one * per character so you can see
# that a paste landed. Handles backspace; Enter ends it.
read_secret() {
  local prompt="$1" secret='' char
  printf '%s' "$prompt" >&2
  while IFS= read -rsn1 char; do
    case "$char" in
      '') break ;;                                    # Enter
      $'\x7f'|$'\b')                                  # backspace
        if [ -n "$secret" ]; then secret="${secret%?}"; printf '\b \b' >&2; fi ;;
      *) secret+="$char"; printf '*' >&2 ;;
    esac
  done
  printf '\n' >&2
  printf '%s' "$secret"
}

if [ -z "${OLLAMA_API_KEY:-}" ]; then
  for f in "$KEY_FILE" "$HOME/.config/ollama/api-key"; do
    if [ -r "$f" ]; then
      OLLAMA_API_KEY="$(tr -d '[:space:]' < "$f")"
      info "key loaded from $f"
      break
    fi
  done
fi

if [ -z "${OLLAMA_API_KEY:-}" ]; then
  [ -t 0 ] || die "OLLAMA_API_KEY is not set and there is no terminal to ask on.
  export OLLAMA_API_KEY=...   or   echo '<key>' > $KEY_FILE && chmod 600 $KEY_FILE
  Keys: https://ollama.com/settings/keys"

  echo >&2
  info "No Ollama.com API key found. Get one at https://ollama.com/settings/keys"
  OLLAMA_API_KEY="$(read_secret 'paste key (hidden, shown as *): ')"
  OLLAMA_API_KEY="$(printf '%s' "$OLLAMA_API_KEY" | tr -d '[:space:]')"
  [ -n "$OLLAMA_API_KEY" ] || die "no key entered"
  info "got ${#OLLAMA_API_KEY} characters"
  KEY_IS_NEW=1
fi
export OLLAMA_API_KEY

# Stop aider falling back to Claude / OpenAI creds that happen to be in the shell.
unset ANTHROPIC_API_KEY ANTHROPIC_API_BASE OPENAI_API_KEY OPENAI_API_BASE

# ---------------------------------------------------------------- fetch catalogue
info "fetching model list from $TAGS_URL ..."
RAW=""
for attempt in 1 2 3; do
  resp="$(curl -sS --max-time 20 -w $'\n%{http_code}' \
            -H "Authorization: Bearer $OLLAMA_API_KEY" "$TAGS_URL" 2>/dev/null)" || resp=""
  code="${resp##*$'\n'}"
  case "$code" in
    200) RAW="${resp%$'\n'*}"; break ;;
    401|403) die "Ollama.com rejected the key (HTTP $code). Check it at https://ollama.com/settings/keys" ;;
    *) info "HTTP ${code:-no response} from $TAGS_URL" ;;
  esac
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

# ---------------------------------------------------------------- verify a new key
# /api/tags is public — it answers 200 for any key, so it proves nothing about
# credentials. The chat endpoint is the only one that actually authenticates, so
# a freshly pasted key gets probed there with a 1-token request.
if [ "${KEY_IS_NEW:-0}" = "1" ]; then
  PROBE_MODEL="$(printf '%s\n' "$ROWS" | awk -F'\t' '
    $1=="gpt-oss:20b" {print $1; found=1; exit}
    $2+0>0 {if (!s || $2+0<s) {s=$2+0; m=$1}}
    END {if (!found && m) print m}')"
  [ -n "$PROBE_MODEL" ] || PROBE_MODEL="${NAMES[0]}"
  info "checking the key against $PROBE_MODEL ..."
  probe_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 \
    -X POST "$OLLAMA_CLOUD_HOST/v1/chat/completions" \
    -H "Authorization: Bearer $OLLAMA_API_KEY" -H 'Content-Type: application/json' \
    -d "{\"model\":\"$PROBE_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":1}" \
    2>/dev/null)" || probe_code=""
  case "$probe_code" in
    200) info "key accepted" ;;
    401|403) die "Ollama.com rejected that key (HTTP $probe_code). Check it at https://ollama.com/settings/keys" ;;
    *) info "warning: could not verify the key (HTTP ${probe_code:-no response}) — carrying on anyway" ;;
  esac

  # Typed in by hand and working — offer to remember it.
  if [ -t 0 ] && [ ! -e "$KEY_FILE" ] && [ "$probe_code" = "200" ]; then
    read -r -p "save it to $KEY_FILE so you don't retype it? [y/N] " save_it
    case "$save_it" in
      [yY]*)
        mkdir -p "$(dirname "$KEY_FILE")"
        ( umask 077; printf '%s\n' "$OLLAMA_API_KEY" > "$KEY_FILE" )
        chmod 600 "$KEY_FILE"
        info "saved to $KEY_FILE (mode 600)" ;;
      *) info "not saved — export OLLAMA_API_KEY to skip this next time" ;;
    esac
  fi
fi

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
