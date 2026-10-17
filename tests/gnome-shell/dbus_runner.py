"""Use GNOME's native headless test infrastructure on isolated D-Bus buses."""
from pathlib import Path
import os
import sys

MUTTER_TESTS = Path(os.environ.get('MUTTER_TESTS_DIR', '/usr/share/mutter-51/tests'))
if not (MUTTER_TESTS / 'mutter_dbusrunner.py').is_file():
    raise RuntimeError('Install mutter-51-tests and python3-dbusmock for GNOME Shell tests')
sys.path.insert(0, str(MUTTER_TESTS))
sys.path.insert(0, str(Path(__file__).resolve().parent / 'upstream'))

from mutter_dbusrunner import meta_run
from gnomeshell_dbusrunner import GnomeShellDBusRunner

if __name__ == '__main__':
    runner = GnomeShellDBusRunner
    if MUTTER_TESTS.name == 'tests' and MUTTER_TESTS.parent.name == 'mutter-14':
        class LegacyRunner(GnomeShellDBusRunner):
            @classmethod
            def setUpClass(klass, enable_kvm, launch):
                super().setUpClass(enable_kvm=enable_kvm, launch=launch)
        runner = LegacyRunner
    sys.exit(meta_run(runner))
