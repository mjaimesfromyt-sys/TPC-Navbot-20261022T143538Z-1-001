import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.preprocessing import TextPreprocessor
from src.embedding import EmbeddingGenerator
from src.vector_store import VectorStore
from src.llm_rag import TPCNavBotRAG

print('===============================================================================')
print('     TALIBON POLYTECHNIC COLLEGE (TPC) NAVBOT AUTOMATED TEST SUITE (PYTHON)    ')
print('===============================================================================\n')

passed = 0
total = 0

def assert_test(condition, test_name):
    global passed, total
    total += 1
    if condition:
        print(f"[PASS] Test {total}: {test_name}")
        passed += 1
    else:
        print(f"[FAIL] Test {total}: {test_name}")

# Test 1: Data Collection Check
raw_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
files = [f for f in os.listdir(raw_dir) if f.endswith('.txt')]
assert_test(len(files) >= 5, f"TPC Raw Dataset contains at least 5 documents (Found: {len(files)})")

# Test 2: Text Preprocessing & Metadata Extraction
processor = TextPreprocessor()
chunks = processor.process_directory(raw_dir)
assert_test(len(chunks) >= 10, f"Text Preprocessor creates at least 10 chunks (Found: {len(chunks)})")
assert_test('building' in chunks[0]['metadata'], 'Chunk metadata contains building field')
assert_test('location_id' in chunks[0]['metadata'], 'Chunk metadata contains location_id field')
assert_test('chunk_id' in chunks[0]['metadata'], 'Chunk metadata contains unique chunk_id')

# Test 3: Embedding Generation
embedder = EmbeddingGenerator()
sample_emb = embedder.embed_text("Where is the Bachelor of Science in Information Systems office?")
assert_test(len(sample_emb) == 384, f"Embedding dimension equals 384 (Found: {len(sample_emb)})")

# Test 4: Distance Metrics Validation
vec_a = embedder.embed_text("BSIS Program Office Room CSC-104")
vec_b = embedder.embed_text("BSIS Department Chair Office CSC-104")
vec_c = embedder.embed_text("Basketball sports gymnasium court")

sim_ab = EmbeddingGenerator.cosine_similarity(vec_a, vec_b)
sim_ac = EmbeddingGenerator.cosine_similarity(vec_a, vec_c)
assert_test(sim_ab > sim_ac, f"Cosine similarity ranks relevant text higher ({sim_ab:.4f} > {sim_ac:.4f})")

dist_ab = EmbeddingGenerator.euclidean_distance(vec_a, vec_b)
dist_ac = EmbeddingGenerator.euclidean_distance(vec_a, vec_c)
assert_test(dist_ab < dist_ac, f"Euclidean distance is smaller for relevant text ({dist_ab:.4f} < {dist_ac:.4f})")

# Test 5: Vector Store Search
vstore = VectorStore(embedder)
vstore.add_chunks(chunks)
hits = vstore.search("Where is the BSIS Program Office?", top_k=3, metric='cosine')
assert_test(len(hits) == 3, 'Vector store returns top-3 search results')
assert_test(hits[0]['score'] > hits[1]['score'], 'Search results are sorted in descending order of similarity score')

# Test 6: Guardrail Safety Check
bot = TPCNavBotRAG()
off_topic_res = bot.query("Explain quantum physics and general relativity")
assert_test(off_topic_res['status'] == 'OFF_TOPIC', 'Guardrail successfully intercepts off-topic query')

# Test 7: Grounded In-Scope Navigation Query
in_scope_res = bot.query("Where is the Bachelor of Science in Criminology (BSCrim) Program Office?")
assert_test(in_scope_res['status'] == 'SUCCESS', 'In-scope query returns SUCCESS status')
assert_test('BSCrim' in in_scope_res['answer'] or 'CRM-102' in in_scope_res['answer'] or len(in_scope_res['sources']) > 0, 'Response includes grounded BSCrim context details')

# Test 8: Unverified Out-of-Dataset Query Check
pool_res = bot.query("Where is the campus swimming pool?")
assert_test(pool_res['status'] == 'UNVERIFIED', 'Out-of-dataset query (swimming pool) returns UNVERIFIED status')

nursing_res = bot.query("Where is the nursing department?")
assert_test(nursing_res['status'] == 'UNVERIFIED', 'Out-of-dataset query (nursing department) returns UNVERIFIED status')

# Test 9: Multi-Turn Conversational Memory & Co-Reference Resolution (Checkpoint 3)
session_test_id = "test_memory_session_01"
turn1 = bot.chat("Where is the BSIS Department Office located?", session_id=session_test_id)
assert_test(turn1['status'] == 'SUCCESS', 'Multi-turn Turn 1 returns SUCCESS')

turn2 = bot.chat("What are its operating hours?", session_id=session_test_id)
assert_test(turn2['status'] == 'SUCCESS', 'Multi-turn Turn 2 successfully resolves pronoun reference ("its")')
assert_test(turn2['turn_count'] == 2, 'Session tracks turn history accurately (turn count = 2)')

# Test 10: Automated Ingestion Pipeline Verification (Checkpoint 3)
from src.ingestion import IngestionPipeline
ingestor = IngestionPipeline()
manifest_check = ingestor.run(force=False)
assert_test(manifest_check['status'] == 'COMPLETED', 'Automated Ingestion Pipeline completes with COMPLETED status')
assert_test(manifest_check['total_documents_scanned'] >= 20, f"Ingestion scans at least 20 raw documents (Found: {manifest_check['total_documents_scanned']})")

print('\n-------------------------------------------------------------------------------')
print(f"TEST SUMMARY: {passed}/{total} TESTS PASSED ({round((passed/total)*100)}% Success Rate)")
print('-------------------------------------------------------------------------------\n')

if passed == total:
    sys.exit(0)
else:
    sys.exit(1)
