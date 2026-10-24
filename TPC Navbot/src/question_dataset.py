"""Inspect a student-question CSV without importing any of its answers as facts.

The compact artifact documents observed question wording and coverage. Runtime
query expansion uses reviewed code constants, never arbitrary CSV instructions.
"""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

from src.campus_entities import normalize
from src.query_understanding import CATEGORY_ENTITIES, INTRODUCTIONS, QUESTION_PATTERNS, understand_query


LANGUAGES = {'English': 'english', 'Filipino': 'tagalog', 'Cebuano': 'bisaya'}
FORBIDDEN_FIELDS = frozenset({'answer', 'referral_guidance', 'hallucination_guard',
                              'system_prompt', 'instructions', 'verified_source', 'location_data'})
MAX_DATASET_BYTES = 64 * 1024 * 1024
MAX_DATASET_ROWS = 50_000


def inspect_question_dataset(path):
    """Return reproducible coverage counts using only question/label columns."""
    path = Path(path)
    if path.stat().st_size > MAX_DATASET_BYTES:
        raise ValueError('Question dataset exceeds the 64 MiB inspection limit')
    rows = 0
    questions = set()
    ids = set()
    languages, categories, facets, mapped_entities = Counter(), Counter(), Counter(), Counter()
    combinations = set()
    recognized = language_agreement = category_agreement = 0
    with path.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if not {'record_id', 'language', 'category', 'question'} <= set(reader.fieldnames or ()):
            raise ValueError('Question dataset requires record_id, language, category and question columns')
        for row in reader:
            rows += 1
            if rows > MAX_DATASET_ROWS:
                raise ValueError('Question dataset exceeds the 50,000-row inspection limit')
            question = row.get('question')
            if not isinstance(question, str) or not question.strip() or len(question) > 600:
                raise ValueError(f'Invalid question at row {rows + 1}')
            record_id = row.get('record_id', '')
            if not record_id or record_id in ids:
                raise ValueError(f'Missing or duplicate question record ID at row {rows + 1}')
            ids.add(record_id)
            questions.add(question)
            language = row.get('language', '')
            category = row.get('category', '')
            languages[language] += 1
            categories[category] += 1
            understanding = understand_query(question)
            if understanding:
                recognized += 1
                facets[understanding.facet] += 1
                mapped_entities[understanding.entity or 'unsupported_school_topic'] += 1
                language_agreement += understanding.language == LANGUAGES.get(language)
                category_agreement += understanding.category == normalize(category)
                combinations.add((understanding.language, understanding.category, understanding.facet))
    return {
        'source_dataset': path.name,
        'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'records': rows,
        'unique_questions': len(questions),
        'duplicate_question_rows': rows - len(questions),
        'languages': dict(sorted(languages.items())),
        'categories': dict(sorted(categories.items())),
        'recognized_patterns': recognized,
        'unrecognized_patterns': rows - recognized,
        'language_label_agreement': language_agreement,
        'category_label_agreement': category_agreement,
        'facet_counts': dict(sorted(facets.items())),
        'mapped_entity_counts': dict(sorted(mapped_entities.items())),
        'observed_language_category_facet_combinations': len(combinations),
        'answer_columns_used': False,
        'fact_indexed': False,
    }


def build_question_patterns(path):
    profile = inspect_question_dataset(path)
    templates = [
        {'language': language, 'facet': facet, 'intent': intent, 'question': question}
        for facet, intent, questions in QUESTION_PATTERNS
        for language, question in zip(('english', 'tagalog', 'bisaya'), questions)
    ]
    return {
        'schema_version': 1,
        'purpose': 'student_question_patterns_only',
        'authority': 'none; wording patterns are not TPC evidence',
        'dataset_profile': profile,
        'templates': templates,
        'introductions': {language: list(items) for language, items in INTRODUCTIONS.items()},
        'supported_categories': sorted(CATEGORY_ENTITIES),
        'limitations': [
            'The dataset has synthetic combinations of a small fixed template vocabulary.',
            'Pattern coverage is not answer accuracy, factual verification or independent generalization.',
            'No answer, alleged referral office or instruction column is imported.',
            'Unknown campus facts still require approved evidence at retrieval time.',
        ],
    }


def load_question_patterns(path):
    """Validate a review artifact; never execute it or use it as campus evidence."""
    path = Path(path)
    if path.stat().st_size > 1_000_000:
        raise ValueError('Question-pattern artifact is too large')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != 1 or data.get('purpose') != 'student_question_patterns_only':
        raise ValueError('Unsupported question-pattern artifact')
    if set(data) != {'schema_version', 'purpose', 'authority', 'dataset_profile', 'templates',
                     'introductions', 'supported_categories', 'limitations'}:
        raise ValueError('Unexpected question-pattern artifact fields')
    if data.get('authority') != 'none; wording patterns are not TPC evidence':
        raise ValueError('Question patterns cannot claim source authority')
    def reject_fact_columns(value):
        if isinstance(value, dict):
            if FORBIDDEN_FIELDS.intersection(value):
                raise ValueError('Question patterns cannot contain facts, answers or instructions')
            for item in value.values():
                reject_fact_columns(item)
        elif isinstance(value, list):
            for item in value:
                reject_fact_columns(item)
    reject_fact_columns(data)
    templates = data.get('templates')
    expected = {(language, facet, intent, question)
                for facet, intent, questions in QUESTION_PATTERNS
                for language, question in zip(('english', 'tagalog', 'bisaya'), questions)}
    if not isinstance(templates, list) or len(templates) > 128:
        raise ValueError('Invalid question templates')
    for item in templates:
        if not isinstance(item, dict) or set(item) != {'language', 'facet', 'intent', 'question'}:
            raise ValueError('Invalid question template record')
        if not all(isinstance(value, str) and len(value) <= 600 for value in item.values()):
            raise ValueError('Invalid question template values')
        if tuple(item[key] for key in ('language', 'facet', 'intent', 'question')) not in expected:
            raise ValueError('Unreviewed question template')
    introductions = data.get('introductions')
    if not isinstance(introductions, dict) or set(introductions) != set(INTRODUCTIONS):
        raise ValueError('Invalid introduction patterns')
    for language, items in introductions.items():
        if not isinstance(items, list) or any(item not in INTRODUCTIONS[language] for item in items):
            raise ValueError('Unreviewed introduction pattern')
    if data.get('supported_categories') != sorted(CATEGORY_ENTITIES):
        raise ValueError('Unreviewed category mapping')
    return data


def write_question_patterns(source_path, output_path):
    from src.storage_io import atomic_write_text
    artifact = build_question_patterns(source_path)
    atomic_write_text(output_path, json.dumps(artifact, ensure_ascii=False, indent=2) + '\n')
    load_question_patterns(output_path)
    return artifact
