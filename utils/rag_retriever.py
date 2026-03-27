import os
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

class RAGRetriever:
    def __init__(self, use_sentence_transformers: bool = True):
        self.use_st = use_sentence_transformers and HAS_SENTENCE_TRANSFORMERS
        self.documents = []
        
        if self.use_st:
            print("Using Sentence-Transformers for RAG embeddings...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embeddings = None
        else:
            print("Using TF-IDF for RAG embeddings...")
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, stop_words='english')
            self.matrix = None
            
    def index_documents(self, documents: List[Dict]):
        """
        Index the provided documents.
        documents should be a list of dicts with 'text' and 'metadata' keys.
        """
        self.documents = documents
        
        if not documents:
            if self.use_st:
                self.embeddings = None
            else:
                self.matrix = None
            return
            
        texts = [doc['text'] for doc in documents]
        
        if self.use_st:
            self.embeddings = self.model.encode(texts, convert_to_numpy=True)
        else:
            self.matrix = self.vectorizer.fit_transform(texts)
            
    def retrieve(self, query: str, top_k: int = 3, min_score: float = 0.2) -> List[Tuple[Dict, float]]:
        """
        Retrieve top_k documents relevant to the query.
        Returns a list of tuples: (document_dict, similarity_score).
        """
        if not self.documents:
            return []
            
        if self.use_st:
            if self.embeddings is None:
                return []
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        else:
            if self.matrix is None:
                return []
            query_vector = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.matrix)[0]
            
        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= min_score:
                results.append((self.documents[idx], score))
                
        return results
