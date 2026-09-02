"""
hashing.py - Streaming MD5 and SHA-256 computation with verification.

Design notes:
- Files are read in CHUNK_SIZE (64 KiB) blocks to support arbitrarily large
  evidence files without loading the entire file into RAM.
- Both MD5 and SHA-256 are computed simultaneously in a single pass.
- Verification returns structured results; original hashes are NEVER
  overwritten during verification (forensic integrity requirement).
- All I/O uses absolute paths from the evidence registry.
"""

import hashlib
import datetime
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

# 64 KiB is a good balance between syscall overhead and memory use.
CHUNK_SIZE = 64 * 1024


@dataclass(frozen=True)
class HashResult:
    """Immutable container for computed hash values."""
    md5: str
    sha256: str

    def to_dict(self) -> dict:
        return {"md5": self.md5, "sha256": self.sha256}


@dataclass(frozen=True)
class VerificationResult:
    """Result of comparing stored vs current hashes."""
    md5_match: bool
    sha256_match: bool
    stored_md5: str
    stored_sha256: str
    current_md5: str
    current_sha256: str

    @property
    def all_match(self) -> bool:
        return self.md5_match and self.sha256_match

    @property
    def status_label(self) -> str:
        return "HASH VERIFIED" if self.all_match else "INTEGRITY WARNING"

    @property
    def status_color(self) -> str:
        return "green" if self.all_match else "red"

    def to_dict(self) -> dict:
        return {
            "md5_match": self.md5_match,
            "sha256_match": self.sha256_match,
            "stored_md5": self.stored_md5,
            "stored_sha256": self.stored_sha256,
            "current_md5": self.current_md5,
            "current_sha256": self.current_sha256,
            "status": self.status_label,
        }


def compute_hashes(file_path: str) -> HashResult:
    """
    Compute MD5 and SHA-256 of the file at `file_path` in a single streaming pass.

    Args:
        file_path: Absolute path to the file.

    Returns:
        HashResult with hex-encoded MD5 and SHA-256.

    Raises:
        FileNotFoundError: File does not exist.
        PermissionError: File cannot be read.
        OSError: Other I/O errors.
    """
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    # Ensure path is absolute and normalized
    p = Path(file_path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Evidence file not found: {file_path}")

    with p.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            md5.update(chunk)
            sha256.update(chunk)

    return HashResult(md5=md5.hexdigest(), sha256=sha256.hexdigest())


def verify_hashes(file_path: str, stored_md5: str, stored_sha256: str) -> VerificationResult:
    """
    Re-compute hashes for `file_path` and compare against stored values.

    This function NEVER overwrites stored hashes. It only compares and
    returns a VerificationResult.

    Args:
        file_path: Absolute path to the evidence file.
        stored_md5: MD5 hash recorded at registration (hex).
        stored_sha256: SHA-256 hash recorded at registration (hex).

    Returns:
        VerificationResult with both stored/current values and match flags.

    Raises:
        FileNotFoundError: File no longer exists.
        PermissionError: File cannot be read.
    """
    current = compute_hashes(file_path)

    return VerificationResult(
        md5_match=(current.md5.lower() == stored_md5.lower()),
        sha256_match=(current.sha256.lower() == stored_sha256.lower()),
        stored_md5=stored_md5,
        stored_sha256=stored_sha256,
        current_md5=current.md5,
        current_sha256=current.sha256,
    )


def compute_and_store(
    file_path: str,
    evidence_id: int,
    conn
) -> HashResult:
    """
    Compute hashes for a file, insert into evidence_hashes, return HashResult.

    This is a transactional helper used during evidence registration.
    Caller is responsible for the outer transaction.

    Args:
        file_path: Absolute path to the evidence file.
        evidence_id: PK of the evidence row just inserted.
        conn: Active SQLite connection (from transaction context).

    Returns:
        HashResult containing the newly computed and stored hashes.
    """
    result = compute_hashes(file_path)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    conn.execute(
        """
        INSERT INTO evidence_hashes (evidence_id, md5_hash, sha256_hash, computed_at, is_original)
        VALUES (?, ?, ?, ?, 1)
        """,
        (evidence_id, result.md5, result.sha256, now_iso),
    )
    return result


# ----------------------------------------------------------------------
# Demo utilities (used by demo_flow.py)
# ----------------------------------------------------------------------

def format_hash_display(md5: str, sha256: str) -> str:
    """Return a formatted multi-line string for hash display in the UI."""
    return (
        f"MD5:\n{md5}\n\n"
        f"SHA-256:\n{sha256}"
    )