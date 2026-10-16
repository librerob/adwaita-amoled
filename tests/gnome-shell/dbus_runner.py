"""Use GNOME's native headless test infrastructure on isolated D-Bus buses."""
from pathlib import Path
import sys

MUTTER_TESTS = Path('/usr/share/mutter-51/tests')
if not (MUTTER_TESTS / 'mutter_dbusrunner.py').is_file():
    raise RuntimeError('Install mutter-51-tests and python3-dbusmock for GNOME Shell tests')
sys.path.insert(0, str(MUTTER_TESTS))
sys.path.insert(0, str(Path(__file__).resolve().parent / 'upstream'))

from mutter_dbusrunner import meta_run
from gnomeshell_dbusrunner import GnomeShellDBusRunner

if __name__ == '__main__':
    sys.exit(meta_run(GnomeShellDBusRunner))
