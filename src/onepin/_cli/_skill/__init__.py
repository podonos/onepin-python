"""Bundled OnePin agent skill (the ``onepin/`` folder is package data, not Python).

This package exists only so ``importlib.resources.files("onepin._cli._skill")`` can resolve
the bundled ``onepin/SKILL.md`` (+ ``reference.md``) in both wheel and zipimport layouts.
``onepin skill install`` copies that folder into each tool's skills directory.
"""
