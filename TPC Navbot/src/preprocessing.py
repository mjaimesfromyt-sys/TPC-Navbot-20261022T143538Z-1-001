"""Text chunks with fail-closed, content-bound campus source provenance."""
import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

from src.config import RAW_DATA_DIR, SOURCE_REGISTRY_PATH

VERIFICATION_SCHEMA = "tpc-source-v1"
APPROVED_SOURCE_TYPES = {"official_document", "official_map", "authorized_campus_record"}
CHUNKER_VERSION = "structural-v3.1"


def _campus_today():
    return datetime.now(timezone(timedelta(hours=8))).date()


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

    def metadata(self, filename, content_bytes, *, registry_entries=None):
        digest = hashlib.sha256(content_bytes).hexdigest()
        # A retrieval operation may reuse one freshly read registry snapshot.
        # Ordinary callers still read the current approval on every call.
        entries = self.entries() if registry_entries is None else registry_entries
        entry = entries.get(Path(filename).name, {})
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
                    valid_date = reviewed <= _campus_today()
                except ValueError:
                    valid_date = False
                if entry.get("sha256") != digest:
                    reason = "content_changed"
                elif fields["source_type"] not in APPROVED_SOURCE_TYPES:
                    reason = "unapproved_source_type"
                elif fields["official_source"] and fields["reviewed_by"] and valid_date:
                    fields["verified_source"] = True
                    reason = "verified"
        # Optional source dates must be usable, rather than silently turning a
        # malformed expiry into an indefinitely current source.
        dates = {}
        if fields["verified_source"]:
            for key in ("publication_date", "effective_date", "valid_until"):
                value = entry.get(key)
                if value not in (None, ""):
                    try:
                        parsed = date.fromisoformat(value) if isinstance(value, str) else None
                    except ValueError:
                        parsed = None
                    if parsed is None or parsed.isoformat() != value:
                        fields["verified_source"] = False
                        reason = "invalid_source_dates"
                        break
                    dates[key] = value
            if (dates.get("effective_date") and dates.get("valid_until")
                    and dates["effective_date"] > dates["valid_until"]):
                fields["verified_source"] = False
                reason = "invalid_source_dates"
        fields["verification_reason"] = reason
        if fields["verified_source"]:
            fields.update(dates)
            # Authority is an operator-supplied review field, never a heading or
            # assertion inside a document. Smaller numbers have higher priority.
            authority = entry.get("source_authority")
            if type(authority) is int and 1 <= authority <= 7:
                fields["source_authority"] = authority
            else:
                fields["source_authority"] = 4 if fields["source_type"] == "authorized_campus_record" else 2
            fields["evidence_status"] = "reviewed"
            for key in ("document_title", "document_version", "academic_year", "category", "intent",
                        "entity", "language", "campus", "department", "section", "review_method"):
                value = review_string(key)
                if value:
                    fields[key] = value
            if "section" in fields:
                fields["section_origin"] = "registry"
            page = entry.get("page")
            if type(page) is int and page > 0 or isinstance(page, str) and page.strip():
                fields["page"] = page if type(page) is int else page.strip()
                fields["page_origin"] = "registry"
            source_url = review_string("source_url")
            try:
                parsed = urlparse(source_url)
                if parsed.scheme in ("http", "https") and parsed.netloc and not parsed.username and not parsed.password:
                    fields["source_url"] = source_url
            except ValueError:
                pass
            supersedes = entry.get("supersedes")
            if isinstance(supersedes, str):
                supersedes = [supersedes]
            if isinstance(supersedes, list):
                names = sorted({name for name in supersedes if isinstance(name, str) and name
                                and Path(name).name == name and "/" not in name and "\\" not in name})
                if names:
                    fields["supersedes"] = json.dumps(names, ensure_ascii=False)
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
    """Keep sections, paragraphs and table headers together in bounded chunks."""

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
        metadata = {
            "source_doc": filename,
            "building": building.group(1).strip() if building else Path(filename).stem.replace("_", " ").title(),
            "location_id": location.group(1).strip() if location else "CAMPUS-GEN-00",
            "verified_source": False,
            "verification_schema": VERIFICATION_SCHEMA,
            "verification_reason": "unregistered",
        }
        # These are literal source labels, not inferred publication facts. Trust
        # remains false until SourceRegistry validates the document's exact bytes.
        for label, key in (("Document Title", "document_title"), ("Title", "document_title")):
            match = re.search(r"^" + label + r":\s*(.+)$", text, re.MULTILINE | re.I)
            if match and key not in metadata:
                metadata[key] = match.group(1).strip()
        return metadata

    @staticmethod
    def _is_heading(line):
        match = re.fullmatch(r"\s*#{1,6}\s+(.+?)\s*#*", line)
        if not match:
            match = re.fullmatch(r"\s*Section\s*:\s*(.+)", line, re.I)
        return match.group(1).strip() if match else None

    @staticmethod
    def _split_body(body, capacity, overlap=0):
        """Split only oversized units; ordinary paragraphs/items stay whole."""
        start = 0
        while start < len(body):
            end = min(start + capacity, len(body))
            if end < len(body):
                # Prefer a complete sentence, then a word, then a hard bound.
                candidates = [m.end() for m in re.finditer(r"[.!?](?:\s|$)", body[start:end])]
                boundary = candidates[-1] + start if candidates else body.rfind(" ", start, end)
                if boundary > start + capacity // 2:
                    end = boundary
            value = body[start:end].strip()
            if value:
                yield value
            if end >= len(body):
                break
            start = max(start + 1, end - overlap)

    @staticmethod
    def _table_separator(line):
        return bool(re.fullmatch(r"\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)+\|?\s*", line))

    def _table_chunks(self, lines, capacity):
        """Repeat a Markdown table's header, or pair oversized rows by column."""
        columns = [cell.strip() for cell in lines[0].strip().strip("|").split("|")]
        table_meta = {"chunk_kind": "table", "table_columns": json.dumps(columns, ensure_ascii=False)}
        table_header = "\n".join(lines[:2])
        current = table_header
        for row_number, row in enumerate(lines[2:], 1):
            if len(table_header) + 1 + len(row) > capacity:
                if current != table_header:
                    yield current, table_meta
                    current = table_header
                cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
                row_label = f"{columns[0]}: {cells[0]}" if columns and cells else ""
                for index, cell in enumerate(cells):
                    label = columns[index] if index < len(columns) else f"Column {index + 1}"
                    context = (row_label + "\n" if index and len(row_label) < capacity // 2 else "") + label + ": "
                    # Keep the complete relationship in metadata even when an
                    # individual column heading itself exceeds a text chunk.
                    prefix = context[:max(1, capacity // 2)]
                    for part in self._split_body(cell, capacity - len(prefix)):
                        yield prefix + part, dict(table_meta, table_row=row_number,
                                                  table_row_label=row_label, table_column=label)
                continue
            proposed = current + "\n" + row
            if len(proposed) > capacity:
                yield current, table_meta
                current = table_header + "\n" + row
            else:
                current = proposed
        if current != table_header:
            yield current, table_meta
        elif len(lines) == 2:
            for part in self._split_body(table_header, capacity):
                yield part, table_meta

    def chunk_text(self, text, metadata):
        cleaned = self.clean_text(text)
        if not cleaned:
            return []
        title = metadata.get("document_title") or metadata['building']
        header = f"Context Source: {title} ({metadata['location_id']})"
        header = header[:min(99, self.chunk_size // 3 - 1)].rstrip() + "\n"
        capacity = self.chunk_size - len(header)
        overlap = min(self.chunk_overlap, capacity // 2)
        chunks, pending = [], []
        section = metadata.get("section")
        page = metadata.get("page")
        section_origin = metadata.get("section_origin")
        page_origin = metadata.get("page_origin")

        def emit(body, extra=None):
            if not body.strip():
                return
            meta = dict(metadata, chunker_version=CHUNKER_VERSION, chunk_kind="paragraph")
            if section:
                meta["section"] = section
                if section_origin:
                    meta["section_origin"] = section_origin
            if page:
                meta["page"] = page
                if page_origin:
                    meta["page_origin"] = page_origin
            meta.update(extra or {})
            meta["chunk_id"] = f"{Path(meta['source_doc']).stem}_chunk_{len(chunks) + 1:04d}"
            chunks.append({"text": header + body, "metadata": meta})

        def flush():
            if pending:
                body = "\n".join(pending)
                for part in self._split_body(body, capacity, overlap):
                    emit(part)
                pending.clear()

        lines = cleaned.splitlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            heading = self._is_heading(line)
            page_label = re.fullmatch(r"\s*(?:\[)?Page\s*:?\s*(\d+)(?:\])?\s*", line, re.I)
            if heading:
                flush()
                section = heading
                section_origin = "document"
                pending.append(line)
                index += 1
                continue
            if page_label:
                flush()
                page = int(page_label.group(1))
                page_origin = "document"
                pending.append(line)
                index += 1
                continue
            if index + 1 < len(lines) and "|" in line and self._table_separator(lines[index + 1]):
                flush()
                table = [line, lines[index + 1]]
                index += 2
                while index < len(lines) and "|" in lines[index] and lines[index].strip():
                    table.append(lines[index])
                    index += 1
                for body, table_metadata in self._table_chunks(table, capacity):
                    emit(body, table_metadata)
                continue
            if not line.strip():
                flush()
                index += 1
                continue
            # Preserve each normal-sized list item/requirement rather than
            # splitting one across unrelated paragraph or section boundaries.
            is_item = bool(re.match(r"\s*(?:[-*+]\s+|\d+[.)]\s+)", line))
            if pending and (is_item or len("\n".join(pending + [line])) > capacity):
                flush()
            pending.append(line)
            index += 1
        flush()
        return chunks

    def process_file(self, filepath, *, registry_entries=None):
        path = Path(filepath)
        raw = path.read_bytes()
        content = raw.decode("utf-8-sig")
        metadata = self.extract_metadata(content, path.name)
        metadata.update(self.registry.metadata(path.name, raw, registry_entries=registry_entries))
        return self.chunk_text(content, metadata)

    def process_directory(self, raw_dir=None):
        chunks = []
        for path in sorted(Path(raw_dir or RAW_DATA_DIR).glob("*.txt")):
            chunks.extend(self.process_file(path))
        return chunks


if __name__ == "__main__":
    chunks = TextPreprocessor().process_directory()
    print(f"Prepared {len(chunks)} chunks; {sum(c['metadata']['verified_source'] for c in chunks)} verified.")
