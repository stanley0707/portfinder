#!/bin/bash
echo "Installing PORTFINDER..."

# Установка через pipx (рекомендуется)
if command -v pipx &> /dev/null; then
    pipx install .
else
    pip install --user .
fi

# Создаём симлинк для глобального доступа
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    ln -sf ~/.local/bin/portfinder /usr/local/bin/portfinder 2>/dev/null || true
    echo "Installation complete. Run 'portfinder --help'"
else
    echo "Installation complete. Run 'portfinder --help' from ~/.local/bin"
fi
