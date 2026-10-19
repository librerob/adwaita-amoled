"""Preserve unittest results and expose failures in GitHub check annotations."""
import os
import subprocess
import sys
import unittest


def main():
    program = unittest.main(verbosity=2, exit=False)
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        for test, traceback in program.result.failures + program.result.errors:
            message = traceback.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
            print(f'::error title={test.id()}::{message}', flush=True)
    sys.exit(0 if program.result.wasSuccessful() else 1)


if __name__ == '__main__':
    # Standalone fixtures can fail before their own exception handler starts,
    # or in an enclosing Xvfb/D-Bus command. Keep the real status and expose the
    # diagnostic tail in check annotations as well as the downloadable run log.
    result = subprocess.run(sys.argv[1:], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    print(result.stdout, end='', flush=True)
    if result.returncode and os.environ.get('GITHUB_ACTIONS') == 'true':
        message = result.stdout[-3000:].replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print(f'::error title=Native command exited {result.returncode}::{message}', flush=True)
    sys.exit(result.returncode if result.returncode >= 0 else 128 - result.returncode)
