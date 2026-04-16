# Compatibility shim — old notebooks import from repo root during transition.
# This file will be deleted once all notebooks are moved to city subfolders
# and use: from lvt import census_utils
from lvt.census_utils import *  # noqa: F401, F403
