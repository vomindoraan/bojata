#!/bin/bash
SRC_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." &>/dev/null && pwd)"
GUI="${1:-1}"
case "$GUI" in
    0) SRC=bojata.py ;;
    1) SRC=bojata_gui.py ;;
    *) echo "Invalid argument"; exit 1 ;;
esac

cd "$SRC_DIR"
export LOGLEVEL=INFO
.venv/bin/python "$SRC" &
sudo renice -n -20 -p $!  # /etc/sudoers.d/bojata
wait $!
