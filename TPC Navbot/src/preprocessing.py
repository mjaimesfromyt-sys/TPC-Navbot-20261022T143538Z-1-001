"""Text chunks with fail-closed, content-bound campus source provenance."""
import hashlib
import json
import re
from datetime import date
from pathlib import Path

from src.config import RAW_DATA_DIR, SOURCE_REGISTRY_PATH

VERIFICATION_SCHEMA = "tpc-source-v1"
APPROVED_SOURCE_TYPES = {"official_document", "official_map", "authorized_campus_record"}


class SourceRegistry:
    """A local human review record, never document-supplied authority.

    Reviewers record an official reference, name, date and exact SHA-256 of the
    reviewed file. Missing/malformed/changed sources fail closed.
    """

    def __init__(self, path=None):
        self.path = Path(path or SOURCE_REGISTRY_PATH)

    def entries(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            documents = data.get("documents", {})
            return documents if isinstance(documents, dict) else {}
        except (OSError, ValueError, TypeError, AttributeError):
            return {}

    def metadata(self, filename, content_bytes):
        digest = hashlib.sha256(content_bytes).hexdigest()
        entry = self.entries().get(Path(filename).name, {})
        if not isinstance(entry, dict):
            entry = {}
        def review_string(key):
            value = entry.get(key, "")
            return value.strip() if isinstance(value, str) else ""

        fields = {
            "source_sha256": digest,
            "verified_source": False,
            "verification_schema": VERIFICATION_SCHEMA,
            "official_source": review_string("official_source"),
            "reviewed_by": review_string("reviewed_by"),
            "reviewed_at": review_string("reviewed_at"),
            "source_type": review_string("source_type") or "unregistered",
        }
        reason = "unregistered"
        if entry:
            reason = "not_reviewed"
            if entry.get("verified") is True:
                reason = "invalid_review"
                try:
                    reviewed = date.fromisoformat(fields["reviewed_at"])
                    valid_date = reviewed <= date.today()
                except ValueError:
                    valid_date = False
                if entry.get("sha256") != digest:
                    reason = "content_changed"
                elif fields["source_type"] not in APPROVED_SOURCE_TYPES:
                    reason = "unapproved_source_type"
                elif fields["official_source"] and fields["reviewed_by"] and valid_date:
                    fields["verified_source"] = True
                    reason = "verified"
        fields["verification_reason"] = reason
        if fields["verified_source"]:
            for key in ("location_data", "route_data"):
                value = entry.get(key)
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except ValueError:
                        continue
                if isinstance(value, dict):
                    fields[key] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        return fields


class TextPreprocessor:
    """Create bounded overlapping chunks while retaining source metadata."""

    def __init__(self, chunk_size=400, chunk_overlap=50, source_registry_path=None):
        if chunk_size < 120 or not 0 <= chunk_overlap < chunk_size // 2:
            raise ValueError("chunk_size must be >=120; overlap must be < half the size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.registry = SourceRegistry(source_registry_path)

    def clean_text(self, text):
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"^[=\-*#]{3,}\s*$", "", text, flags=re.MULTILINE)
        abbreviations = {"Bldg": "Building", "Rm": "Room", "Dept": "Department", "Admin": "Administration", "Lvl": "Level"}
        for short, full in abbreviations.items():
            text = re.sub(r"\b" + short + r"\b", full, text, flags=re.IGNORECASE)
        text = re.sub(r"[ \t]+", " ", text)
        return re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text).strip()

    def extract_metadata(self, text, source_filename):
        building = re.search(r"^Building Name:\s*(.+)$", text, re.MULTILINE)
        location = re.search(r"^Location ID:\s*(.+)$", text, re.MULTILINE)
        filename = Path(source_filename).name
        return {
            "source_doc": filename,
            "building": building.group(1).strip() if building else Path(filename).stem.replace("_", " ").title(),
            "location_id": location.group(1).strip() if location else "CAMPUS-GEN-00",
            "verified_source": False,
            "verification_schema": VERIFICATION_SCHEMA,
            "verification_reason": "unregistered",
        }

    def chunk_text(self, text, metadata):
        cleaned = self.clean_text(text)
        if not cleaned:
            return []
        header = f"Context Source: {metadata['building']} ({metadata['location_id']})\n"
        header = header[:min(100, self.chunk_size // 3)]
        capacity = self.chunk_size - len(header)
        overlap = min(self.chunk_overlap, capacity // 2)
        chunks, start = [], 0
        while start < len(cleaned):
            end = min(start + capacity, len(cleaned))
            if end < len(cleaned):
                boundary = cleaned.rfind(" ", start + capacity // 2, end)
                if boundary > start:
                    end = boundary
            body = cleaned[start:end].strip()
            if body:
                meta = metadata.copy()
                meta["chunk_id"] = f"{Path(meta['source_doc']).stem}_chunk_{len(chunks) + 1:04d}"
                chunks.append({"text": header + body, "metadata": meta})
            if end >= len(cleaned):
                break
            start = max(start + 1, end - overlap)
        return chunks

    def process_file(self, filepath):
        path = Path(filepath)
        raw = path.read_bytes()
        content = raw.decode("utf-8-sig")
        metadata = self.extract_metadata(content, path.name)
        metadata.update(self.registry.metadata(path.name, raw))
        return self.chunk_text(content, metadata)

    def process_directory(self, raw_dir=None):
        chunks = []
        for path in sorted(Path(raw_dir or RAW_DATA_DIR).glob("*.txt")):
            chunks.extend(self.process_file(path))
        return chunks


if __name__ == "__main__":
    chunks = TextPreprocessor().process_directory()
    print(f"Prepared {len(chunks)} chunks; {sum(c['metadata']['verified_source'] for c in chunks)} verified.")
