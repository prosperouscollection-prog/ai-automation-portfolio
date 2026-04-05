#!/bin/bash
MESSAGE="$1"
osascript -e "tell application \"Messages\" to send \"$MESSAGE\" to buddy \"+13134002575\""
