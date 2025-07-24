from poetry.core.masonry.builders.sdist import SdistBuilder
from poetry.factory import Factory


# 1. Загружаем конфиг через сам Poetry
poetry = Factory().create_poetry(".")
package = poetry.package

# 2. Автоматически генерируем setup.py
if __name__ == "__main__":
    builder = SdistBuilder(poetry)
    builder.build()
