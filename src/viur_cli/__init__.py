# viur-cli v3 — package marker only.
#
# Submodules are imported explicitly by `cli.py`'s `main()` entry point.
# The v2 pattern of `from .X import *` here triggered module-level side
# effects (conf.py auto-loading project.json, sys.exit on missing files)
# which is now avoided.
