Development Setup (macOS / Linux / Windows from Source)
=======================================================

This section describes how to run MUIO from source for development purposes.
These steps are intended for contributors and research teams working on macOS,
Linux, or Windows without using the packaged `.exe`.

Prerequisites
-------------

- Python 3.9+
- Git
- GLPK and CBC solvers installed on the system
- pip (Python package installer)

macOS (Apple Silicon or Intel)
------------------------------

1. Install solvers using Homebrew:

   .. code-block:: bash

      brew install glpk
      brew install coin-or-tools/coinor/cbc

   Note: `cbc` is keg-only. Add it to your PATH:

   .. code-block:: bash

      echo 'export PATH="/opt/homebrew/opt/cbc/bin:$PATH"' >> ~/.zshrc
      source ~/.zshrc

2. Create a virtual environment:

   .. code-block:: bash

      python3 -m venv venv
      source venv/bin/activate

3. Install dependencies:

   .. code-block:: bash

      pip install --upgrade pip
      pip install -r requirements.txt

4. Start the application:

   .. code-block:: bash

      python API/app.py

5. Open in browser:

   http://127.0.0.1:5002

Linux (Ubuntu/Debian)
---------------------

1. Install solvers:

   .. code-block:: bash

      sudo apt update
      sudo apt install glpk-utils coinor-cbc

2. Create virtual environment:

   .. code-block:: bash

      python3 -m venv venv
      source venv/bin/activate

3. Install dependencies:

   .. code-block:: bash

      pip install --upgrade pip
      pip install -r requirements.txt

4. Run the server:

   .. code-block:: bash

      python API/app.py

5. Open in browser:

   http://127.0.0.1:5002

Windows (From Source)
---------------------

The recommended approach for Windows users is to use the packaged `.exe`.
However, running from source is also possible:

1. Install Python 3.9+
2. Install GLPK and CBC and ensure they are available on PATH.
3. Create virtual environment:

   .. code-block:: bash

      python -m venv venv
      venv\Scripts\activate

4. Install dependencies:

   .. code-block:: bash

      pip install --upgrade pip
      pip install -r requirements.txt

5. Run:

   .. code-block:: bash

      python API/app.py

Important Notes
---------------

Solver Detection
~~~~~~~~~~~~~~~~

On macOS/Linux, MUIO automatically detects `glpsol` and `cbc`
from the system PATH. Environment variable overrides are also supported:

- ``MUIO_GLPK_PATH``
- ``MUIO_CBC_PATH``

requirements.txt Encoding
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``requirements.txt`` file is encoded in UTF-16LE.
`pip install -r requirements.txt` handles this correctly.
Some external tools may require converting the file to UTF-8.

File Permissions (macOS/Linux)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Config.py` contains:

.. code-block:: python

   os.chmod(DATA_STORAGE, 0o777)

This runs at import time. If permission errors occur,
ensure the ``WebAPP/DataStorage`` directory exists and
has appropriate write permissions.
