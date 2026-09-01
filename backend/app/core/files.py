"""
File validation helpers for document uploads (Phase 4).

Security rules implemented here:
  * MIME whitelist (server-side, not filename-based)
  * magic-byte signature check (never trust the declared/extension type alone)
  * filename sanitisation (no path separators, no traversal, safe characters)
"""

import re

MAX_FILE_NAME_LENGTH = 120

# Controlled document types (docs/requirements.md).
DOCUMENT_TYPES: frozenset[str] = frozenset(
    {
        "FIR",
        "POLICE_REPORT",
        "INVESTIGATION_REPORT",
        "WITNESS_STATEMENT",
        "EVIDENCE_RECORD",
        "FORENSIC_REPORT",
        "CHARGE_SHEET",
        "COURT_FILING",
        "LEGAL_NOTICE",
        "JUDGMENT",
        "OTHER",
    }
)

# Simple confidentiality classification set for the prototype.
CLASSIFICATIONS: frozenset[str] = frozenset(
    {"PUBLIC", "INTERNAL", "RESTRICTED", "CONFIDENTIAL"}
)

# Allowed upload MIME types (PDF, images, and common office/text documents).
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "text/plain",
        "text/csv",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
)

# Magic-byte signatures for binary formats we can verify cheaply.
_MAGIC: dict[str, bytes] = {
    "application/pdf": b"%PDF-",
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
    # OLE2 container (legacy .doc/.xls)
    "application/msword": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    "application/vnd.ms-excel": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
}
# OOXML types (.docx/.xlsx) are ZIP containers.
_ZIP_TYPES: frozenset[str] = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
)


def signature_matches(content_type: str, head: bytes) -> bool:
    """
    Verify the file's leading bytes look like the declared content type.

    Returns False when the declared type's signature is absent — i.e. the
    client claimed one format but sent another. Text formats (txt/csv) are
    accepted as-is (no meaningful binary signature).
    """
    if content_type in _MAGIC:
        return head.startswith(_MAGIC[content_type])
    if content_type in _ZIP_TYPES:
        return head.startswith(b"PK\x03\x04")
    # text/plain, text/csv: nothing reliable to sniff — accept.
    return True


def sanitize_filename(name: str) -> str:
    """
    Return a safe filename:
      * strips any directory components (prevents path traversal)
      * keeps only A-Z a-z 0-9 . _ - (others → "_")
      * no leading dots (blocks "..", hidden files)
      * bounded length
    """
    name = name.replace("\\", "/")
    name = name.rsplit("/", 1)[-1]  # basename only
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = name.lstrip(".") or "upload.bin"
    return name[:MAX_FILE_NAME_LENGTH] or "upload.bin"
