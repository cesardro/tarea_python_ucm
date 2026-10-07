from pathlib import Path
import pytest

if __name__ == '__main__':
    # Runs every test file of this folder (tests/), as run_all_tests.py of funciones_pk
    pytest.main([str(Path(__file__).parent)])
