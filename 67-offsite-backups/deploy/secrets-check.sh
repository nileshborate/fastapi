#!/usr/bin/env bash
# Video 67 - ON THE SERVER: where are the secrets - and who can read them?
#   deploy/secrets-check.sh        exit 1 if ANY of them can be read by everybody
set -uo pipefail
bad=0
for f in "$HOME/coursehub/.env" "$HOME/slack_url" "$HOME/pager_url" "$HOME/restic.env" \
         "$HOME/restic-password" "$HOME/.ssh/authorized_keys"; do
    [ -e "$f" ] || continue
    mode=$(stat -c %a "$f")
    who=$(stat -c %U:%G "$f")
    if (( 8#$mode & 8#004 )); then           # the last digit: "others" - every user on the box
        echo "!!! $f  $mode  $who - EVERY user on this server can read it"
        bad=1
    else
        echo "ok  $f  $mode  $who"
    fi
done
exit $bad
