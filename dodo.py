"""Doit autogeneration."""

import glob
from doit.task import clean_targets
from shutil import rmtree
import os

DOIT_CONFIG = {
    'default_tasks': ['html'],
    'cleandep': True
}


def task_pot():
    """Re-create .pot."""
    return {
            'actions': ['pybabel extract -o "./locale/mood.pot" -k _:2 -k ngettext:2,3 mood'],
            'file_dep': glob.glob('mood/*.py'),
            'targets': ['./locale/mood.pot'],
            'clean': True
           }


def task_po():
    """Update translations."""
    return {
            'actions': [
                'pybabel update --ignore-pot-creation-date -D mood -d locale -i locale/mood.pot -l ru_RU.UTF-8'
            ],
            'file_dep': ['./locale/mood.pot'],
            'targets': ['./locale/ru_RU.UTF-8/LC_MESSAGES/mood.po'],
           }


def task_mo():
    """Compile translations."""
    return {
            'actions': [
                (os.makedirs, ["mood/ru_RU.UTF-8/LC_MESSAGES"], {"exist_ok": True}),
                'pybabel compile -d mood -D mood -l ru_RU.UTF-8 -i locale/ru_RU.UTF-8/LC_MESSAGES/mood.po'
            ],
            'file_dep': ['./locale/ru_RU.UTF-8/LC_MESSAGES/mood.po'],
            'targets': ['./mood/ru_RU.UTF-8/LC_MESSAGES/mood.mo'],
            'clean': True
           }


def task_i18n():
    """Auto-creation locale."""
    return {
        'actions': None,
        'task_dep': ['pot', 'po', 'mo']
    }


def task_test():
    """Run tests."""
    return {
        'actions': [
            'python3 -m unittest ./tests/test_server.py',
            'python3 -m unittest ./tests/test_client.py'
        ],
        'file_dep': ["./tests/test_server.py", "./tests/test_client.py"],
        'task_dep': ['i18n']
    }


def task_html():
    """Crete docs html."""
    return {
        'actions': ['sphinx-build -M html ./docs/source ./mood/docs/build'],
        'file_dep': glob.glob("./docs/source/*.rst"),
        'targets': ['./mood/docs/build'],
        'clean': [clean_build, clean_targets],
    }


def task_sdist():
    """Build source distribution."""
    return {
            'actions': ['python -m build --sdist'],
            'task_dep': ['erase'],
    }


def task_wheel():
    """Make wheele."""
    return {
            'actions': ['python -m build -w'],
            'task_dep': ['i18n', 'html'],
            'doc': 'generate wheel',
    }


def clean_build():
    """Remove docs generates."""
    if os.path.exists('./mood/docs/build'):
        rmtree("./mood/docs/build")


def task_erase():
    """Remove uncommit file."""
    return {
            'actions': ['git clean -xdf']
    }
