import time
import hashlib
import numpy as np
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False
    
# Global cache instance
_cache_instance = None

class SemanticCache:
    def __init__(self, ttl_minutes=60, similarity_threshold=0.85):
        self.ttl = timedelta(minutes=ttl_minutes)
        self.threshold = similarity_threshold
        # Cache list elements: {'hash': str, 'norm_query': str, 'embedding': ndarray, 'response': dict/str, 'expires_at': datetime}
        self.cache = []
        
        self.model = None
        if HAS_ST:
            print("[Cache] Loading minimal SentenceTransformer for Semantic Caching...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            print("[Cache] SentenceTransformer not found. Running in Exact-Match Mode only.")

    def _normalize(self, text: str) -> str:
        return " ".join(text.lower().strip().split())

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _cleanup(self):
        """Remove expired cache entries."""
        now = datetime.utcnow()
        self.cache = [entry for entry in self.cache if entry['expires_at'] > now]

    def get_cached_response(self, user_query: str):
        """
        Check if the query matches the cache.
        Returns (response, strategy) where strategy is 'exact', 'semantic', or None.
        """
        self._cleanup()
        if not user_query or not self.cache:
            return None, None
            
        norm_q = self._normalize(user_query)
        q_hash = self._hash(norm_q)
        
        # 1. Check Exact Match via Hash
        for entry in self.cache:
            if entry['hash'] == q_hash:
                print(f"[Cache] Exact hit for hash: {q_hash[:8]}")
                return entry['response'], "exact"
                
        # 2. Check Semantic Match via Cosine Similarity
        if self.model is not None and self.cache:
            try:
                # Filter entries that actually have embeddings
                valid_entries = [e for e in self.cache if e['embedding'] is not None]
                if not valid_entries:
                    return None, None
                    
                q_emb = self.model.encode([norm_q], convert_to_numpy=True)
                stored_embs = np.vstack([e['embedding'] for e in valid_entries])
                
                sims = cosine_similarity(q_emb, stored_embs)[0]
                best_idx = np.argmax(sims)
                best_score = float(sims[best_idx])
                
                if best_score >= self.threshold:
                    print(f"[Cache] Semantic hit (score: {best_score:.2f})")
                    return valid_entries[best_idx]['response'], "semantic"
            except Exception as e:
                print(f"[Cache] Semantic matching error: {e}")
                
        return None, None

    def add_to_cache(self, user_query: str, response):
        """Stores the given mapping into the cache."""
        self._cleanup()
        norm_q = self._normalize(user_query)
        q_hash = self._hash(norm_q)
        
        emb = None
        if self.model is not None:
            try:
                emb = self.model.encode([norm_q], convert_to_numpy=True)[0]
            except Exception:
                pass
                
        entry = {
            'hash': q_hash,
            'norm_query': norm_q,
            'embedding': emb,
            'response': response,
            'expires_at': datetime.utcnow() + self.ttl
        }
        self.cache.append(entry)
        print(f"[Cache] Saved '{norm_q[:30]}...' to cache. Total cached: {len(self.cache)}")


def get_cache_instance() -> SemanticCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SemanticCache()
    return _cache_instance
