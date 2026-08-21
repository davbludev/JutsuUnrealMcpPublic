#!/usr/bin/env python3
"""Entry point an agent host launches as a stdio MCP server.

Configure it with any Python 3 interpreter the machine already has - the one on PATH, or the one
the engine ships at ``Engine/Binaries/ThirdParty/Python3/<Platform>/python.exe``. The CLI never
searches for an interpreter: by the time any of its code runs, one has already been chosen.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jutsu_mcp.stdio import main  # noqa: E402  (path setup has to precede the import)

if __name__ == "__main__":
    sys.exit(main())
