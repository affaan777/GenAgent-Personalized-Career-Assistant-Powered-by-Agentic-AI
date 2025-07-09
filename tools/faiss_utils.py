import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os
import threading

class FaissHandler:
    """
    Modular FAISS handler supporting multiple data types (e.g., resume, course).
    Each data type has its own index and corpus for safe separation and retrieval.
    """
    def __init__(self, embedding_model_name="all-MiniLM-L6-v2", dimension=384, base_dir="."):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.dimension = dimension
        self.base_dir = base_dir
        self._locks = {}
        self._indices = {}
        self._corpora = {}
        self._loaded_types = set()

    def _get_index_file(self, data_type):
        return os.path.join(self.base_dir, f"faiss_index_{data_type}.bin")

    def _get_corpus_file(self, data_type):
        return os.path.join(self.base_dir, f"faiss_corpus_{data_type}.pkl")

    def _ensure_loaded(self, data_type):
        if data_type in self._loaded_types:
            return
        # Thread safety for loading
        if data_type not in self._locks:
            self._locks[data_type] = threading.Lock()
        with self._locks[data_type]:
            if data_type in self._loaded_types:
                return
            # Load or create index
            index_file = self._get_index_file(data_type)
            if os.path.exists(index_file):
                index = faiss.read_index(index_file)
            else:
                index = faiss.IndexFlatL2(self.dimension)
            self._indices[data_type] = index
            # Load or create corpus
            corpus_file = self._get_corpus_file(data_type)
            if os.path.exists(corpus_file):
                with open(corpus_file, 'rb') as f:
                    corpus = pickle.load(f)
            else:
                corpus = []
            self._corpora[data_type] = corpus
            self._loaded_types.add(data_type)

    def save(self, data_type):
        """Save FAISS index and corpus for a data type."""
        self._ensure_loaded(data_type)
        index_file = self._get_index_file(data_type)
        corpus_file = self._get_corpus_file(data_type)
        faiss.write_index(self._indices[data_type], index_file)
        with open(corpus_file, 'wb') as f:
            pickle.dump(self._corpora[data_type], f)

    def add(self, text: str, meta: dict, data_type: str):
        """Add a new item (with text and meta) to the index for a data type."""
        self._ensure_loaded(data_type)
        if not text.strip():
            return "⚠️ Empty text, cannot embed."
        embedding = self.embedding_model.encode([text])[0]
        embedding = np.array([embedding]).astype("float32")
        self._indices[data_type].add(embedding)
        self._corpora[data_type].append((text, meta))
        self.save(data_type)
        return "✅ Stored in FAISS."

    def search(self, query_text: str, data_type: str, top_k: int = 3, filter_fn=None):
        """Search for similar items in the index for a data type. Optionally filter results with filter_fn(meta)."""
        self._ensure_loaded(data_type)
        corpus = self._corpora[data_type]
        if not corpus:
            return []
        query_embedding = self.embedding_model.encode([query_text])
        query_embedding = np.array(query_embedding).astype("float32")
        D, I = self._indices[data_type].search(query_embedding, top_k)
        results = []
        for idx, i in enumerate(I[0]):
            if i < len(corpus):
                text, meta = corpus[i]
                distance = D[0][idx]
                similarity_score = 1 - distance
                if filter_fn is None or filter_fn(meta):
                    results.append({
                        "text": text,
                        "meta": meta,
                        "similarity": similarity_score
                    })
        return results

    def get_corpus(self, data_type: str):
        """Get the full corpus for a data type."""
        self._ensure_loaded(data_type)
        return self._corpora[data_type]

    def clear(self, data_type: str):
        """Clear the index and corpus for a data type."""
        self._indices[data_type] = faiss.IndexFlatL2(self.dimension)
        self._corpora[data_type] = []
        self.save(data_type)

    def migrate_legacy_data(self, legacy_index_file="faiss_index.bin", legacy_corpus_file="faiss_corpus.pkl", target_data_type="resume"):
        """
        Migrate legacy FAISS data to the new modular format.
        Preserves existing data and maintains backward compatibility.
        """
        legacy_index_path = os.path.join(self.base_dir, legacy_index_file)
        legacy_corpus_path = os.path.join(self.base_dir, legacy_corpus_file)
        
        if not (os.path.exists(legacy_index_path) and os.path.exists(legacy_corpus_path)):
            print("⚠️ No legacy data found to migrate.")
            return False
        
        try:
            # Load legacy data
            legacy_index = faiss.read_index(legacy_index_path)
            with open(legacy_corpus_path, 'rb') as f:
                legacy_corpus = pickle.load(f)
            
            # Convert legacy format to new format
            self._ensure_loaded(target_data_type)
            
            # Copy index vectors
            vectors = legacy_index.reconstruct_n(0, legacy_index.ntotal)
            self._indices[target_data_type].add(vectors)
            
            # Convert corpus format: (text, filename) -> (text, {"filename": filename})
            for text, filename in legacy_corpus:
                meta = {"filename": filename}
                self._corpora[target_data_type].append((text, meta))
            
            # Save in new format
            self.save(target_data_type)
            
            print(f"✅ Migrated {len(legacy_corpus)} items to '{target_data_type}' data type")
            print(f"   Legacy files preserved: {legacy_index_file}, {legacy_corpus_file}")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False

    def search_with_clickable_links(self, query_text: str, data_type: str, top_k: int = 3, exclude_filename=None):
        """
        Search with backward-compatible clickable links format.
        Maintains the same output format as the original get_similar_texts function.
        """
        results = self.search(query_text, data_type, top_k)
        
        if not results:
            return "📝 No items found in the database."
        
        formatted_results = []
        for i, result in enumerate(results):
            meta = result["meta"]
            filename = meta.get("filename", "unknown")
            similarity_percentage = result["similarity"] * 100
            
            # Skip if it's the same file
            if exclude_filename and filename == exclude_filename:
                continue
            
            # Create clickable link (assuming resume files)
            if data_type == "resume":
                clean_name = self._clean_filename(filename)
                markdown_link = f"[📄 {clean_name}](http://192.168.1.10:8000/static/resumes/{filename})"
                formatted_results.append(f"{markdown_link} - **{similarity_percentage:.1f}% Match**")
            else:
                # For other data types, just show the title/name
                title = meta.get("title", meta.get("filename", "Unknown"))
                formatted_results.append(f"📄 {title} - **{similarity_percentage:.1f}% Match**")
        
        if not formatted_results:
            return "📝 No similar items found in the database."
        
        # Format the results nicely
        final_results = "\n\n".join([f"{i+1}. {result}" for i, result in enumerate(formatted_results)])
        return f"🔗 **Similar {data_type.title()} Found:**\n\n{final_results}"

    def _clean_filename(self, filename: str) -> str:
        """Extract a clean, readable filename from UUID filename."""
        if '_' in filename:
            parts = filename.split('_', 1)
            if len(parts) > 1:
                clean_name = parts[1]
                clean_name = os.path.splitext(clean_name)[0]
                clean_name = clean_name.replace('-', ' ').replace('_', ' ')
                clean_name = ' '.join(word.capitalize() for word in clean_name.split())
                return clean_name
        
        clean_name = os.path.splitext(filename)[0]
        clean_name = clean_name.replace('-', ' ').replace('_', ' ')
        clean_name = ' '.join(word.capitalize() for word in clean_name.split())
        return clean_name

# Backward compatibility functions
def embed_and_store(text: str, filename: str) -> str:
    """Legacy function for backward compatibility."""
    handler = FaissHandler()
    # Migrate legacy data if needed
    if not handler.get_corpus("resume"):
        handler.migrate_legacy_data()
    
    meta = {"filename": filename}
    return handler.add(text, meta, "resume")

def get_similar_texts(query_text: str, filename: str, top_k: int = 3) -> str:
    """Legacy function for backward compatibility."""
    handler = FaissHandler()
    # Migrate legacy data if needed
    if not handler.get_corpus("resume"):
        handler.migrate_legacy_data()
    
    return handler.search_with_clickable_links(query_text, "resume", top_k, exclude_filename=filename)

# Example usage:
# handler = FaissHandler()
# handler.add("This is a resume text", {"filename": "resume1.pdf"}, data_type="resume")
# handler.add("This is a course description", {"course_id": "course1"}, data_type="course")
# results = handler.search("data science", data_type="course", top_k=5) 