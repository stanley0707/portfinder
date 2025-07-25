from pathlib import Path

from poetry.core.masonry.builders.sdist import SdistBuilder
from poetry.factory import Factory


poetry = Factory().create_poetry(Path("."))
package = poetry.package


if __name__ == "__main__":
    builder = SdistBuilder(poetry)
    builder.build()
