"""Module that executes code standardization and functionality tests."""

from subprocess import run
from sys import argv, exit


def run_checks(target: str) -> None:
    """Execute all code checks internally in sequence.

    Order: isort → black → pydocstyle → doctest → mypy → pytest

    Parameters
    ----------
    target : str
        The target file or directory.
    """
    commands = [
        ['isort', '--only-modified', '--profile', 'black', target],
        ['black', '--skip-string-normalization', target],
        ['pydocstyle', target],
        ['python', '-m', 'doctest', target],
        ['mypy', '--namespace-packages', '--explicit-package-bases', target],
        ['pytest', '--verbose'],
    ]

    for command in commands:
        result = run(command)
        if result.returncode != 0:
            print(
                f'Command {' '.join(command)} failed with exit code {result.returncode}'
            )
            exit(result.returncode)


if __name__ == '__main__':
    target = argv[1] if len(argv) > 1 else '.'
    run_checks(target)
