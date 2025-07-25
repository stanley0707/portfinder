#!/bin/bash
echo "Installing PORTFINDER..."

if command -v pipx &> /dev/null; then
    pipx install .
else
    pip install --user .
fi

if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    ln -sf ~/.local/bin/portfinder /usr/local/bin/portfinder 2>/dev/null || true
    echo "Installation complete. Run 'portfinder --help'"
else
    echo "Installation complete. Run 'portfinder --help' from ~/.local/bin"
fi
