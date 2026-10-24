"""Select reviewed evidence by authority, explicit time and source supersession.

Review dates are provenance, never publication/effective dates. Missing dates
cannot establish a historical fact. These helpers do not create campus facts.
"""
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import re


def campus_today():
    return datetime.now(timezone(timedelta(hours=8))).date()


def iso_date(value):
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def requested_period(query):
    for match in re.finditer(r"\b((?:19|20)\d{2})(?:\s*[-–/]\s*((?:19|20)\d{2}))?\b", query):
        if re.search(r'\b(?:room|rm|silid|lawak|code)\s*[#-]?\s*$', query[:match.start()], re.I):
            continue
        return int(match[1]), int(match[2] or match[1])
    return None


def source_authority(metadata):
    value = metadata.get('source_authority')
    if type(value) is int and 1 <= value <= 7:
        return value
    return 2 if metadata.get('source_type') in {'official_document', 'official_map'} else 4


def applicable(metadata, query, *, today=None):
    today = today or campus_today()
    start = iso_date(metadata.get('effective_date'))
    end = iso_date(metadata.get('valid_until'))
    published = iso_date(metadata.get('publication_date'))
    period = requested_period(query)
    if period:
        first, last = date(period[0], 1, 1), date(period[1], 12, 31)
        academic = requested_period(str(metadata.get('academic_year', '')))
        if (start and start > last) or (end and end < first) or (published and published > last):
            return False
        # A publication date by itself does not prove a time-sensitive rule
        # remained effective in a different year.
        if academic:
            return academic == period
        if start:
            return start <= last and (end is None or end >= first)
        return bool(published and first <= published <= last)
    academic = requested_period(str(metadata.get('academic_year', '')))
    return not ((start and start > today) or (end and end < today)
                or (published and published > today)
                or (academic and not academic[0] <= today.year <= academic[1]))


def _supersedes(metadata):
    value = metadata.get('supersedes', [])
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            value = []
    return value if isinstance(value, list) else []


def select_current_records(records, query, *, fields=None, language='english'):
    """Filter only applicable records; never silently settle peer conflicts."""
    candidates = [record for record in records if applicable(record['_hit']['metadata'], query)]
    removed = set()
    for new in candidates:
        new_meta = new['_hit']['metadata']
        for old in candidates:
            old_meta = old['_hit']['metadata']
            if old_meta.get('source_doc') in _supersedes(new_meta) and source_authority(new_meta) <= source_authority(old_meta):
                removed.add(old_meta.get('source_doc'))
            # An explicitly dated later version of the same titled document
            # can replace its previous version for current (not historical) use.
            if not requested_period(query) and new_meta.get('document_title') and new_meta.get('document_title') == old_meta.get('document_title'):
                newer, older = iso_date(new_meta.get('effective_date')), iso_date(old_meta.get('effective_date'))
                if (newer and older and newer > older and new_meta.get('document_version')
                        and old_meta.get('document_version') and source_authority(new_meta) <= source_authority(old_meta)):
                    removed.add(old_meta.get('source_doc'))
    candidates = [record for record in candidates if record['_hit']['metadata'].get('source_doc') not in removed]
    if candidates and fields:
        supported = [record for record in candidates if any(
            field_value(record, field, language) not in (None, '', [], {}) for field in fields)]
        if supported:
            candidates = supported
        strongest = min(source_authority(record['_hit']['metadata']) for record in candidates)
        candidates = [record for record in candidates if source_authority(record['_hit']['metadata']) == strongest]
    return candidates


def claim_fields(query, intent, facet=None):
    if facet:
        return ('details.' + facet,)
    if intent == 'contact':
        return ('contact',)
    q = query.casefold()
    specific = (
        ('fees', r'\b(?:fee|fees|tuition|how much|magkano|pila ang bayad)\b'),
        ('deadlines', r'\b(?:deadline|deadlines|last day)\b'),
        ('online_option', r'\b(?:online|remote|remotely)\b'),
        ('staff', r'\b(?:who is|who are|coordinator|dean|kinsa|sino)\b'),
    )
    for field, pattern in specific:
        if re.search(pattern, q):
            return ('details.' + field,)
    if intent in ('location', 'route'):
        if re.search(r'\b(?:which|what) floor\b|unsang andana|anong palapag', q):
            return ('floor',)
        if re.search(r'\b(?:which|what) room\b|room number|unsang lawak|anong silid', q):
            return ('room',)
        return ('building', 'floor', 'room', 'location', 'route_data') if intent == 'route' else ('building', 'floor', 'room', 'location')
    return (intent,) if intent in ('hours', 'services', 'contact', 'accessibility') else ()


def field_value(record, path, language):
    if path == 'route_data':
        return record['_hit']['metadata'].get('route_data')
    value = record
    for part in path.split('.'):
        value = value.get(part) if isinstance(value, dict) else None
    if isinstance(value, dict):
        value = value.get(language)
    return value


def conflicting_fields(records, fields, language):
    conflicts = []
    for field in fields:
        seen = {}
        for record in records:
            value = field_value(record, field, language)
            if value in (None, '', [], {}):
                continue
            normalized = json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()
            seen.setdefault(normalized, set()).add(record['_hit']['metadata']['source_doc'])
        # Multiple locations within a single directory remain a destination
        # clarification. Conflicting sources require explicit disclosure.
        if len(seen) > 1 and len(set.union(*seen.values())) > 1:
            conflicts.append(field)
    return conflicts


def source_detail(record, fields=()):
    metadata = record['_hit']['metadata']
    detail = {'destination': record['destination']}
    # A whole structured record is carried by each chunk. A heading inferred
    # for an unrelated chunk must not become a fabricated claim locator.
    field_texts = []
    def collect(value):
        if isinstance(value, dict):
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, (str, int, float)) and not isinstance(value, bool):
            field_texts.append(' '.join(str(value).casefold().split()))
    for field in fields:
        value = record
        for part in field.split('.'):
            value = value.get(part) if isinstance(value, dict) else None
        collect(value)
    text = ' '.join(record['_hit'].get('text', '').casefold().split())
    chunk_supports_claim = bool(field_texts) and all(value in text for value in field_texts)
    for key in ('source_doc', 'official_source', 'reviewed_by', 'reviewed_at',
                'source_sha256', 'source_type', 'review_method', 'evidence_status',
                'source_authority', 'source_url', 'document_title', 'document_version',
                'publication_date', 'effective_date', 'valid_until', 'academic_year', 'page', 'section'):
        if key in metadata and metadata[key] not in (None, ''):
            if key in {'page', 'section'} and metadata.get(key + '_origin') == 'document' and metadata.get('location_data') and not chunk_supports_claim:
                continue
            detail[key] = metadata[key]
    if fields:
        fields = [field for field in fields if (record['_hit']['metadata'].get('route_data') if field == 'route_data' else
                  record.get('details', {}).get(field.split('.', 1)[1]) if field.startswith('details.') and isinstance(record.get('details'), dict) else
                  record.get(field)) not in (None, '', [], {})]
        detail['claim_fields'] = list(fields)
        detail['verified_fact_ids'] = [hashlib.sha256(
            f"{metadata.get('source_sha256', '')}|{record['destination']}|{field}".encode('utf-8')).hexdigest()[:24]
            for field in fields]
    return detail
