#!/usr/bin/env bash
#
# rotate-logs.sh — size-based log rotation for boxes without logrotate.
#
# Truncates in place instead of renaming the live file, so processes holding an
# open file descriptor keep writing to the same inode and nothing has to be
# restarted or sent SIGHUP.

set -euo pipefail

KEEP=5
SIZE_KB=10240
PATTERN='*.log'
DRY_RUN=0

usage() {
  cat <<'EOF'
usage: rotate-logs.sh [options] DIRECTORY

options:
  -k, --keep N       generations to keep (default: 5)
  -s, --size KB      rotate files larger than this, in KB (default: 10240)
  -p, --pattern GLOB filename glob to consider (default: *.log)
  -n, --dry-run      print what would happen, change nothing
  -h, --help         this text

example:
  rotate-logs.sh --keep 3 --size 5120 /var/log/myapp
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -k|--keep)    KEEP="${2:?--keep needs a value}"; shift 2 ;;
    -s|--size)    SIZE_KB="${2:?--size needs a value}"; shift 2 ;;
    -p|--pattern) PATTERN="${2:?--pattern needs a value}"; shift 2 ;;
    -n|--dry-run) DRY_RUN=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    --)           shift; break ;;
    -*)           printf 'unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
    *)            break ;;
  esac
done

DIR="${1:-}"
[[ -n "$DIR" ]] || { usage >&2; exit 2; }
[[ -d "$DIR" ]] || { printf 'not a directory: %s\n' "$DIR" >&2; exit 1; }
[[ "$KEEP" =~ ^[0-9]+$ && "$KEEP" -ge 1 ]] || { printf 'keep must be >= 1\n' >&2; exit 2; }
[[ "$SIZE_KB" =~ ^[0-9]+$ ]] || { printf 'size must be an integer\n' >&2; exit 2; }

run() {
  if (( DRY_RUN )); then
    printf 'would: %s\n' "$*"
  else
    "$@"
  fi
}

rotate_one() {
  local file="$1" i

  # The oldest generation falls off the end.
  if [[ -e "$file.$KEEP.gz" ]]; then
    run rm -f "$file.$KEEP.gz"
  fi

  for (( i = KEEP - 1; i >= 1; i-- )); do
    if [[ -e "$file.$i.gz" ]]; then
      run mv "$file.$i.gz" "$file.$((i + 1)).gz"
    fi
  done

  run cp "$file" "$file.1"
  run truncate -s 0 "$file"
  run gzip -f "$file.1"
  printf 'rotated %s\n' "$file"
}

found=0
while IFS= read -r -d '' file; do
  found=1
  rotate_one "$file"
done < <(find "$DIR" -maxdepth 1 -type f -name "$PATTERN" -size +"${SIZE_KB}"k -print0)

if (( ! found )); then
  printf 'nothing matching %s over %sKB in %s\n' "$PATTERN" "$SIZE_KB" "$DIR"
fi
