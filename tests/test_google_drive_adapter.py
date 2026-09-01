"""
Only tests the query-escaping helper — constructing a real GoogleDriveAdapter
triggers googleapiclient's discovery-document fetch, which needs network
access and shouldn't run in unit tests.
"""

from srma_cloud.adapters.google_drive import _escape_query_value


def test_escapes_single_quote():
    assert _escape_query_value("O'Brien") == "O\\'Brien"


def test_escapes_backslash_before_quote():
    # backslash must be escaped first, or an already-escaped quote's
    # backslash would itself be (incorrectly) re-escaped
    assert _escape_query_value("a\\'b") == "a\\\\\\'b"


def test_leaves_plain_ids_unchanged():
    assert _escape_query_value("1A2b3C_folderId") == "1A2b3C_folderId"
