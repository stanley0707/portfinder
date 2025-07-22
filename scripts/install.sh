#!/bin/bash
echo "Installing PORTEX..."

# Установка через pipx (рекомендуется)
if command -v pipx &> /dev/null; then
    pipx install .
else
    pip install --user .
fi

# Создаём симлинк для глобального доступа
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    ln -sf ~/.local/bin/portex /usr/local/bin/portex 2>/dev/null || true
    echo "Installation complete. Run 'portex --help'"
else
    echo "Installation complete. Run 'portex --help' from ~/.local/bin"
fi
