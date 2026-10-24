"""Export traceable facts and Q&A from current provenance-approved TPC sources.

Question CSV answers are never read. This is a derived review/retrieval artifact,
not a model training job and not independent authentication of campus sources.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.config import RAW_DATA_DIR, SOURCE_REGISTRY_PATH
from src.evidence import campus_today, conflicting_fields, select_current_records
from src.llm_rag import TPCNavBotRAG
from src.preprocessing import TextPreprocessor
from src.storage_io import atomic_write_text


LANGUAGES = ('english', 'tagalog', 'bisaya')
FIELDS = ('building', 'floor', 'room', 'location', 'hours', 'services', 'contact', 'accessibility')
CONFIDENCE = 'reviewed source; not independently authenticated'
TEMPLATES = {
    'building': ('Which building is the {name} in?', 'Saang gusali ang {name}?', 'Unsang building ang {name}?'),
    'floor': ('Which floor is the {name} on?', 'Saang palapag ang {name}?', 'Unsang andana ang {name}?'),
    'room': ('What is the {name} room number?', 'Ano ang numero ng silid ng {name}?', 'Unsa ang numero sa lawak sa {name}?'),
    'location': ('Where is the {name}?', 'Nasaan ang {name}?', 'Asa dapit ang {name}?'),
    'hours': ('What are the {name} office hours?', 'Ano ang oras ng {name}?', 'Unsa ang oras sa {name}?'),
    'services': ('What services does the {name} offer?', 'Ano ang serbisyo ng {name}?', 'Unsa ang serbisyo sa {name}?'),
    'contact': ('Who should I contact about the {name}?', 'Sino ang dapat kontakin tungkol sa {name}?', 'Kinsa ang kontakon bahin sa {name}?'),
    'accessibility': ('Is the {name} wheelchair accessible?', 'Accessible ba sa wheelchair ang {name}?', 'Accessible ba sa wheelchair ang {name}?'),
}


class _NoRetrieval:
    def search(self, *args, **kwargs):
        return []


def _status(metadata):
    method = metadata.get('review_method', '')
    if method == 'location_confirmation_reported_by_user':
        return 'direct_user_confirmation'
    if method == 'school_confirmation_reported_by_user':
        return 'reviewed_user_reported'
    return 'reviewed_source'


def _meaningful(value):
    return value not in (None, '', [], {}) and not isinstance(value, bool)


def _fields(record):
    fields = {field: record[field] for field in FIELDS if _meaningful(record.get(field))}
    details = record.get('details')
    if isinstance(details, dict):
        fields.update({f'details.{key}': value for key, value in details.items()
                       if isinstance(key, str) and _meaningful(value)})
    return fields


def _provenance(record):
    meta = record['_hit']['metadata']
    page_section = meta.get('section', '')
    if meta.get('page') not in (None, ''):
        page = f"page {meta['page']}"
        page_section = f'{page}; {page_section}' if page_section else page
    return {
        'entity': record['destination'],
        'category': meta.get('category', 'campus_information'),
        'evidence_status': _status(meta),
        'source': meta.get('official_source', ''),
        'source_url': meta.get('source_url', ''),
        'document': meta['source_doc'],
        'source_sha256': meta['source_sha256'],
        'page_or_section': page_section,
        'publication_date': meta.get('publication_date', ''),
        'effective_date': meta.get('effective_date', ''),
        'document_version': meta.get('document_version', ''),
        'valid_until': meta.get('valid_until', ''),
        'last_verified': meta.get('reviewed_at', ''),
        'reviewed_by': meta.get('reviewed_by', ''),
        'confidence': CONFIDENCE,
    }


def build_verified_qa(*, raw_data_dir=None, source_registry_path=None):
    raw = Path(raw_data_dir or RAW_DATA_DIR).resolve()
    registry_path = Path(source_registry_path or SOURCE_REGISTRY_PATH)
    processor = TextPreprocessor(source_registry_path=registry_path)
    entries = processor.registry.entries()
    renderer = TPCNavBotRAG(vector_store=_NoRetrieval(), initialize_knowledge_base=False, use_llm=False)
    records_by_entity = defaultdict(list)
    approved_documents = set()
    skipped_documents = Counter()
    for source in sorted(raw.glob('*.txt')):
        try:
            content = source.read_bytes()
            metadata = processor.extract_metadata(content.decode('utf-8-sig'), source.name)
            metadata.update(processor.registry.metadata(source.name, content, registry_entries=entries))
        except (OSError, UnicodeError, ValueError):
            skipped_documents['unreadable'] += 1
            continue
        if not metadata.get('verified_source'):
            skipped_documents[metadata.get('verification_reason', 'unreviewed')] += 1
            continue
        hit = {'id': source.name, 'score': 1.0, 'text': content.decode('utf-8-sig'), 'metadata': metadata}
        if not renderer._approved(hit):
            skipped_documents['invalid_provenance'] += 1
            continue
        approved_documents.add(source.name)
        for record in renderer._records(hit):
            if record.get('restricted') is True:
                skipped_documents['restricted_record'] += 1
                continue
            entity = renderer._entity(record['destination']) or record['destination'].casefold()
            records_by_entity[entity].append(record)

    candidates = {}
    collisions = set()
    conflicts = []
    current_documents = set()
    for entity, records in sorted(records_by_entity.items()):
        selected = select_current_records(records, f'Current {entity} at TPC')
        fields_for_entity = sorted({field for record in selected for field in _fields(record)})
        field_sources = {}
        for field in fields_for_entity:
            by_language = {language: select_current_records(records, f'Current {entity} at TPC',
                           fields=(field,), language=language) for language in LANGUAGES}
            field_sources[field] = by_language
        for record in selected:
            metadata = record['_hit']['metadata']
            current_documents.add(metadata['source_doc'])
            provenance = _provenance(record)
            for field, value in _fields(record).items():
                by_language = field_sources[field]
                if not any(any(item['_hit']['metadata']['source_doc'] == metadata['source_doc']
                               for item in localized) for localized in by_language.values()):
                    continue
                # A conflict is retained in the manifest rather than silently
                # being published as a verified answer from either peer source.
                if any(conflicting_fields(by_language[language], (field,), language) for language in LANGUAGES):
                    conflict = {'entity': entity, 'field': field,
                                'documents': sorted({item['_hit']['metadata']['source_doc'] for item in selected})}
                    if conflict not in conflicts:
                        conflicts.append(conflict)
                    continue
                fact_id = hashlib.sha256(f"{metadata['source_sha256']}|{record['destination']}|{field}".encode('utf-8')).hexdigest()[:24]
                if fact_id in candidates and candidates[fact_id][0]['value'] != value:
                    collisions.add(fact_id)
                    continue
                fact = {'verified_fact_id': fact_id, 'field': field, 'value': value, **provenance}
                candidates[fact_id] = (fact, record)

    facts, qa = [], []
    for fact_id, (fact, record) in sorted(candidates.items()):
        if fact_id in collisions:
            continue
        facts.append(fact)
        field = fact['field']
        if field not in TEMPLATES:
            continue
        intent = 'location' if field in {'building', 'floor', 'room', 'location'} else field
        # Each answer uses exactly one exported field, giving its singular
        # verified_fact_id a precise relationship to all factual answer text.
        single_field = {'destination': record['destination'], '_hit': record['_hit'], field: fact['value']}
        for index, language in enumerate(LANGUAGES):
            status, answer = renderer._render_record(single_field, language, intent, None)
            if status != 'SUCCESS':
                continue
            qa.append({
                'record_id': f'qa-{fact_id}-{language}', 'language': language,
                'category': fact['category'], 'intent': intent,
                'question': TEMPLATES[field][index].format(name=record['destination']),
                'answer': answer, 'verified_fact_id': fact_id,
                'verified_fact_ids': [fact_id], 'field': field,
                'evidence_status': fact['evidence_status'], 'source': fact['source'],
                'source_url': fact['source_url'], 'document': fact['document'],
                'source_sha256': fact['source_sha256'],
                'page_or_section': fact['page_or_section'],
                'publication_date': fact['publication_date'], 'effective_date': fact['effective_date'],
                'document_version': fact['document_version'], 'confidence': CONFIDENCE,
                'referral_guidance': '', 'last_verified': fact['last_verified'],
                'answer_language_note': 'Reviewed source wording is preserved; a missing translation is not invented.',
            })
            if language == 'bisaya' and field == 'location':
                mixed = dict(qa[-1])
                mixed.update(record_id=f'qa-{fact_id}-mixed', language='mixed',
                             question=f'Asa ang {record["destination"]} location?')
                qa.append(mixed)
    manifest = {
        'schema_version': 1, 'purpose': 'derived_verified_source_facts_and_qa',
        'created_on': campus_today().isoformat(),
        'source_registry_sha256': hashlib.sha256(registry_path.read_bytes()).hexdigest(),
        'approved_document_count': len(approved_documents),
        'current_document_count': len(current_documents),
        'current_documents': sorted(current_documents),
        'facts': len(facts), 'qa_records': len(qa),
        'languages': dict(sorted(Counter(row['language'] for row in qa).items())),
        'evidence_status_counts': dict(sorted(Counter(row['evidence_status'] for row in facts).items())),
        'excluded_documents': dict(sorted(skipped_documents.items())),
        'conflicts': conflicts, 'ambiguous_fact_id_collisions': sorted(collisions),
        'question_dataset_answers_used': False, 'model_weight_updates': False,
        'limitations': [
            'Approval and authority are locally recorded reviews, not independent school authentication.',
            'Publication/effective dates, URLs and page references remain empty when not supplied.',
            'Q&A answers quote approved field values; missing translations preserve reviewed source wording.',
            'Derived artifacts must be rebuilt after raw source or registry changes; runtime revalidates original sources.',
            'Only explicitly supported fields are exported; this is not proof all student questions are answerable.',
        ],
    }
    return {'facts': facts, 'qa': qa, 'manifest': manifest}


def write_verified_qa(output_dir, **kwargs):
    bundle = build_verified_qa(**kwargs)
    output = Path(output_dir)
    for key, filename in (('facts', 'facts.jsonl'), ('qa', 'qa.jsonl')):
        atomic_write_text(output / filename, ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in bundle[key]))
    atomic_write_text(output / 'manifest.json', json.dumps(bundle['manifest'], ensure_ascii=False, indent=2) + '\n')
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=PROJECT_ROOT / 'data/verified_qa')
    parser.add_argument('--raw-data-dir', type=Path, default=RAW_DATA_DIR)
    parser.add_argument('--source-registry', type=Path, default=SOURCE_REGISTRY_PATH)
    args = parser.parse_args()
    bundle = write_verified_qa(args.output_dir, raw_data_dir=args.raw_data_dir, source_registry_path=args.source_registry)
    print(json.dumps(bundle['manifest'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
