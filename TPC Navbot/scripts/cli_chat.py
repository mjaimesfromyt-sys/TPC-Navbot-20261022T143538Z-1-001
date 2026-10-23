import time
import sys
import os
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.llm_rag import TPCNavBotRAG

def main():
    bot = TPCNavBotRAG()
    session_id = str(uuid4())

    print('===============================================================================')
    print('                 TPC NAVBOT: CAMPUS NAVIGATION ASSISTANT                        ')
    print('             Gen AI Capstone Project - Checkpoints 1 & 2 Demo (Python)          ')
    print('===============================================================================')
    print('Welcome! Ask me anything about TPC campus locations, room numbers, office hours,')
    print('tuition payments, IT support, library facilities, or campus policies.')
    print('Only reviewed TPC information is answered. Sample locations are unverified.')
    print('Type "exit" or "quit" to end the session.\n')

    while True:
        try:
            user_input = input('\n[User Question] > ').strip()
            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit']:
                print('\nThank you for using TPC NavBot! Have a great day on campus.')
                break

            print('\n[TPC NavBot Thinking...] Searching vector database...')
            start_time = time.time()
            response = bot.chat(user_input, session_id=session_id)
            elapsed_ms = int((time.time() - start_time) * 1000)

            print(f"\n--- TPC NavBot Response (Latency: {elapsed_ms}ms | Status: {response['status']}) ---")
            print(response['answer'])
            if response.get('sources'):
                print('\nSources:')
                details = response.get('source_details', [])
                if details:
                    for source in details:
                        print(f"- {source['source_doc']} — {source['official_source']} ({source['reviewed_at']})")
                else:
                    for source in response['sources']:
                        print(f'- {source}')
            print('-------------------------------------------------------------------------------\n')

        except (KeyboardInterrupt, EOFError):
            print('\nSession ended. Goodbye!')
            break

if __name__ == "__main__":
    main()
