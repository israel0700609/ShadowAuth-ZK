"""
Root-level pytest configuration.

Adds the project's source directories to sys.path so that the non-package
imports used in src/crypto/ resolve correctly:

  - `from common import constants`  → needs   src/        in sys.path
  - `import poseidon_wrapper`        → needs   src/crypto/ in sys.path
  - `import merkle_tree`             → needs   src/crypto/ in sys.path
  - `import key_manager`             → needs   src/crypto/ in sys.path
"""

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "src", "crypto"))
