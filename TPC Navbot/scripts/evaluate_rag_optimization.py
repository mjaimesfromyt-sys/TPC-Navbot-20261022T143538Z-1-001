"""Offline question-pattern, source-citation and hybrid retrieval evaluation.

CSV answer/referral columns are never read as expected facts. The 10k wording
rows collapse into 1,500 language/topic/facet groups for answer evaluation.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.evidence import field_value
from src.llm_rag import TPCNavBotRAG
from src.question_dataset import inspect_question_dataset
from src.query_understanding import understand_query
from scripts.evaluate_school_qa import build_cases, build_offline_bot, evaluate


class RetrievalView:
    def __init__(self, store, hybrid):
        self.store, self.hybrid = store, hybrid

    def __getattr__(self, key):
        return getattr(self.store, key)

    def search(self, query, top_k=3, metric='cosine'):
        return self.store.search(query, top_k=top_k, metric=metric, hybrid=self.hybrid)


def citation_problems(response, store, bot):
    problems = []
    if response['status'] == 'SUCCESS' and not response['source_details']:
        problems.append('successful factual answer has no source')
    for detail in response['source_details']:
        matching = [meta for meta in store.metadatas if meta.get('source_doc') == detail.get('source_doc')]
        if not matching or not all(meta.get('verified_source') for meta in matching):
            problems.append('citation is not an approved source')
            continue
        records = bot._records({'score': 1, 'metadata': matching[0]})
        records = [record for record in records if record['destination'] == detail['destination']]
        if not records:
            problems.append('citation names a different destination')
        for field in detail.get('claim_fields', []):
            if not any(field_value(record, field, response['language']) not in (None, '', [], {}) for record in records):
                problems.append('cited field has no source value: ' + field)
        for key in ('source_sha256', 'source_url', 'publication_date', 'effective_date', 'page', 'section'):
            if key in detail and detail[key] != matching[0].get(key):
                # Sections/page may differ across actual structured chunks.
                if not any(meta.get(key) == detail[key] for meta in matching):
                    problems.append('citation metadata differs from its source: ' + key)
    return problems


def retrieval_metrics(bot, store, hybrid):
    recall, precision, reciprocal_rank = [], [], []
    for case in build_cases():
        if not case.source_groups or case.preceding:
            continue
        entity, intent = bot._entity(case.query), bot._intent(case.query)
        if not entity or not intent:
            continue
        hits = store.search(f'{entity} {intent} TPC', top_k=max(20, len(store.documents)), hybrid=hybrid)
        documents = list(dict.fromkeys(hit['metadata']['source_doc'] for hit in hits))[:3]
        def relevant(name, group):
            return any(name.startswith(f'school_confirmed_{number:02}_') for number in group)
        recall.append(sum(any(relevant(name, group) for name in documents) for group in case.source_groups) / len(case.source_groups))
        precision.append(sum(any(relevant(name, group) for group in case.source_groups) for name in documents) / max(1, len(documents)))
        rank = next((index for index, name in enumerate(documents, 1) if any(relevant(name, group) for group in case.source_groups)), None)
        reciprocal_rank.append(1 / rank if rank else 0)
    average = lambda items: round(sum(items) / len(items), 6) if items else None
    return {'cases': len(recall), 'unique_documents_k': 3, 'recall_at_3': average(recall),
            'precision_at_3': average(precision), 'mrr_at_3': average(reciprocal_rank)}


def run(dataset, *, baseline_module=None):
    started = time.monotonic()
    profile = inspect_question_dataset(dataset)
    groups = {}
    with Path(dataset).open(encoding='utf-8-sig', newline='') as source:
        for row in csv.DictReader(source):
            question = row['question']
            understood = understand_query(question)
            key = (understood.language, understood.category, understood.facet) if understood else ('unrecognized', question)
            group = groups.setdefault(key, {'question': question, 'count': 0})
            group['count'] += 1
    with tempfile.TemporaryDirectory(prefix='tpc-rag-evaluation-') as directory:
        bot = build_offline_bot(Path(directory))
        store = bot.vector_store
        # This offline benchmark owns an immutable in-memory index. Validate
        # every source once, then check the complete corpus fingerprint again
        # at the end. Live retrieval still revalidates bytes on every request.
        def corpus_fingerprint():
            files = sorted(Path(store.raw_data_dir).glob('*.txt')) + [Path(store.source_registry_path)]
            return hashlib.sha256(b''.join(path.name.encode('utf-8') + b'\0' + path.read_bytes() for path in files)).hexdigest()
        corpus_before = corpus_fingerprint()
        verified_rows = list(store._verified_rows())
        store._verified_rows = lambda: iter(verified_rows)
        before = None
        if baseline_module:
            spec = importlib.util.spec_from_file_location('tpc_baseline_rag', baseline_module)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            before = module.TPCNavBotRAG(vector_store=RetrievalView(store, False), initialize_knowledge_base=False, use_llm=False)
        weighted, unique, previous = Counter(), Counter(), Counter()
        language_correct = 0
        cited, citation_ok, successful, missing_facet_successes = 0, 0, 0, 0
        issues, examples = [], []
        for index, (key, group) in enumerate(groups.items(), 1):
            question, count = group['question'], group['count']
            understood = understand_query(question)
            response = bot.query(question)
            weighted[response['status']] += count
            unique[response['status']] += 1
            language_correct += count * bool(understood and response['language'] == understood.language)
            if before:
                previous[before.query(question)['status']] += count
            problems = citation_problems(response, store, bot)
            if response['source_details']:
                cited += 1
                citation_ok += not problems
            successful += response['status'] == 'SUCCESS'
            if response['status'] == 'SUCCESS' and understood and understood.facet in {
                    'online_option', 'schedule', 'eligibility', 'appointment', 'status', 'first_step',
                    'correction', 'change_information', 'follow_up', 'lost_item'}:
                expected = 'details.' + understood.facet
                if not all(expected in detail.get('claim_fields', []) for detail in response['source_details']):
                    missing_facet_successes += 1
            if problems:
                issues.append({'question': question, 'problems': problems, 'status': response['status']})
            if len(examples) < 30 or problems:
                examples.append({'question': question, 'weight': count, 'status': response['status'],
                                 'language': response['language'], 'answer': response['answer'],
                                 'source_details': response['source_details']})
            if index % 250 == 0:
                print(f'Checked {index}/{len(groups)} unique question groups', flush=True)
        retrieval = {'vector_only': retrieval_metrics(bot, store, False), 'hybrid': retrieval_metrics(bot, store, True)}
        if corpus_fingerprint() != corpus_before:
            raise RuntimeError('The corpus changed during evaluation; discard this run and repeat it.')
    school = evaluate()
    return {
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'mode': 'offline lexical embeddings + BM25; LLM disabled; no model/weight updates',
        'corpus_snapshot_sha256': corpus_before,
        'dataset': profile,
        'answer_evaluation': {'unique_groups': len(groups), 'weighted_rows': sum(group['count'] for group in groups.values()),
                              'weighted_statuses': dict(weighted), 'unique_statuses': dict(unique),
                              'baseline_weighted_statuses': dict(previous) if before else None,
                              'response_language_label_agreement': language_correct,
                              'successful_groups': successful, 'cited_groups': cited,
                              'citation_contract_passed_groups': citation_ok,
                              'citation_contract_failures': issues,
                              'unsupported_facet_successes': missing_facet_successes},
        'retrieval': retrieval,
        'reviewed_school_benchmark': {'passed': school['passed'], 'total': school['total'],
                                      'failures': [row for row in school['results'] if not row['passed']]},
        'examples': examples,
        'duration_seconds': round(time.monotonic() - started, 2),
        'limitations': [
            'The CSV contains synthetic combinations of 60 core questions, not 10,000 independent facts.',
            'Each exact CSV question is classified; answer checks are weighted over 1,500 language/topic/facet groups.',
            'CSV answers, referral names, and guard instructions are excluded from facts and answer labels.',
            'Citation contracts check source identity, hashes and field support; they are not independent semantic grading.',
            'No authoritative answers exist for many dataset topics; UNVERIFIED is an appropriate result.',
            'All real approved sources currently record user-reported school review or direct user confirmation.',
            'Unknown publication/effective dates, handbook pages and source URLs remain absent.',
            'Lexical-mode tests do not establish multilingual semantic-model quality or universal hallucination rates.',
            'Answer evaluation uses a frozen approved corpus snapshot with source fingerprints checked before and after; live retrieval revalidates every request.',
            'The optional saved baseline uses the same current reviewed index with vector-only retrieval; original chunking is not replayed.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--baseline-module', type=Path)
    parser.add_argument('--output', type=Path, default=PROJECT_ROOT / 'data/evaluation/rag_optimization.json')
    args = parser.parse_args()
    report = run(args.dataset, baseline_module=args.baseline_module)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('answer_evaluation', 'retrieval', 'reviewed_school_benchmark', 'duration_seconds')}, ensure_ascii=False, indent=2))
    print(f'Report: {args.output}')
    if report['answer_evaluation']['citation_contract_failures'] or report['answer_evaluation']['unsupported_facet_successes'] or report['reviewed_school_benchmark']['failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
