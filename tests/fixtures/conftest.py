"""Keep pytest from collecting the sample fixture repos.

Files under ``tests/fixtures/`` (e.g. ``test_app.py``, ``*.test.ts``) are
*inputs* for the scanner/renderer, not tests to run. ``testpaths = ["tests"]``
would otherwise recurse here and collect them.
"""

collect_ignore_glob = ["*"]
