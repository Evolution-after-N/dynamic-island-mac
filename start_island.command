#!/bin/zsh
osascript -e 'tell application "Terminal" to set miniaturized of front window to true'
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
python3 island.py
