"""Preserve unittest results and expose failures in GitHub check annotations."""
import os
import sys
import unittest


def main():
    program = unittest.main(verbosity=2, exit=False)
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        for test, traceback in program.result.failures + program.result.errors:
            message = traceback.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
            print(f'::error title={test.id()}::{message}', flush=True)
    sys.exit(0 if program.result.wasSuccessful() else 1)
