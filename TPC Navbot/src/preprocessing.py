import os
import re
import glob

class TextPreprocessor:
    """
    Handles text cleaning, normalization, metadata extraction, and chunking
    for the TPC NavBot campus knowledge base.
    """
    def __init__(self, chunk_size=400, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.abbreviations = {
            r'\bBldg\b': 'Building',
            r'\bBLDG\b': 'Building',
            r'\bRm\b': 'Room',
            r'\bRM\b': 'Room',
            r'\bDept\b': 'Department',
            r'\bDEPT\b': 'Department',
            r'\bAdmin\b': 'Administration',
            r'\bLvl\b': 'Level',
            r'\bExt\.\b': 'Extension',
            r'\bHQ\b': 'Headquarters'
        }

    def clean_text(self, text: str) -> str:
        """
        Cleans raw document text by stripping ASCII divider decorations,
        normalizing whitespace, and expanding abbreviations.
        """
        # Remove ASCII horizontal divider lines (================, ---------------)
        cleaned = re.sub(r'^[=\-*#]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        # Expand known campus abbreviations
        for pattern, replacement in self.abbreviations.items():
            cleaned = re.sub(pattern, replacement, cleaned)
            
        # Replace multiple spaces/newlines with clean single space / double newline
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        return cleaned.strip()

    def extract_metadata(self, text: str, source_filename: str) -> dict:
        """
        Extracts key header metadata (Building Name, Location ID) from document header.
        """
        building_match = re.search(r'Building Name:\s*(.+)', text)
        location_match = re.search(r'Location ID:\s*(.+)', text)
        
        building = building_match.group(1).strip() if building_match else os.path.basename(source_filename).replace('.txt', '').replace('_', ' ').title()
        location_id = location_match.group(1).strip() if location_match else "CAMPUS-GEN-00"
        
        return {
            "source_doc": os.path.basename(source_filename),
            "building": building,
            "location_id": location_id
        }

    def chunk_text(self, text: str, metadata: dict) -> list:
        """
        Recursively chunks text into overlapping blocks while preserving metadata headers.
        """
        cleaned = self.clean_text(text)
        paragraphs = [p.strip() for p in cleaned.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = f"Context Source: {metadata['building']} ({metadata['location_id']})\n"
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 1 <= self.chunk_size:
                current_chunk += para + "\n"
            else:
                if len(current_chunk.strip()) > 50:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "metadata": metadata.copy()
                    })
                # Start new chunk with overlap from last paragraph
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) >= self.chunk_overlap else ""
                current_chunk = f"Context Source: {metadata['building']} ({metadata['location_id']})\n" + overlap_text + para + "\n"
                
        if len(current_chunk.strip()) > 50:
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": metadata.copy()
            })
            
        # Assign unique chunk_ids
        for idx, chunk in enumerate(chunks):
            doc_stem = metadata['source_doc'].replace('.txt', '')
            chunk['metadata']['chunk_id'] = f"{doc_stem}_chunk_{idx+1:03d}"
            
        return chunks

    def process_directory(self, raw_dir: str) -> list:
        """
        Processes all .txt files in raw_dir and returns flat list of chunk dictionaries.
        """
        all_chunks = []
        files = glob.glob(os.path.join(raw_dir, "*.txt"))
        for filepath in sorted(files):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            meta = self.extract_metadata(content, filepath)
            doc_chunks = self.chunk_text(content, meta)
            all_chunks.extend(doc_chunks)
        return all_chunks


if __name__ == "__main__":
    raw_path = r"c:\Users\ranz\Desktop\TPC Navbot\data\raw"
    processor = TextPreprocessor()
    chunks = processor.process_directory(raw_path)
    print(f"Preprocessed {len(chunks)} total text chunks from {raw_path}.")
    if chunks:
        print("\n--- SAMPLE CHUNK ---")
        print(f"ID: {chunks[0]['metadata']['chunk_id']}")
        print(f"Metadata: {chunks[0]['metadata']}")
        print(f"Text Snippet:\n{chunks[0]['text'][:200]}...")
