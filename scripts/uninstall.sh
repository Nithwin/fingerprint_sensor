#!/bin/bash
# Fingerprint Lock Screen — Uninstaller

APP_NAME="fingerprint-lock"

echo "Uninstalling Fingerprint Lock Screen..."

rm -f "$HOME/.local/bin/$APP_NAME"
rm -f "$HOME/.local/bin/${APP_NAME}-enroll"
rm -rf "$HOME/.local/share/$APP_NAME"
rm -f "$HOME/.local/share/applications/$APP_NAME-settings.desktop"
rm -rf "$HOME/.config/fingerprint-lock"

echo "✅ Uninstalled successfully."
