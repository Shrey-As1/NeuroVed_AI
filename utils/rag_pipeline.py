import os
from typing import Dict
from utils.rag_loader import load_documents
from utils.rag_chunker import process_documents
from utils.rag_retriever import RAGRetriever
from utils.rag_prompt_builder import build_rag_prompt
from utils.gemini_api import ask_gemini

# Initialize global retriever
_retriever = None

def init_rag_system(kb_dir: str = 'data/knowledge_base'):
    """
    Initialize the RAG system by loading, chunking, and indexing the Knowledge Base.
    """
    global _retriever
    print(f"Initializing RAG system from {kb_dir}...")
    
    # Load docs
    raw_docs = load_documents(kb_dir)
    print(f"Loaded {len(raw_docs)} documents.")
    
    # Chunk docs
    chunked_docs = process_documents(raw_docs, chunk_size=500, overlap=50)
    print(f"Created {len(chunked_docs)} chunks from documents.")
    
    # Initialize Retriever
    _retriever = RAGRetriever(use_sentence_transformers=True)
    _retriever.index_documents(chunked_docs)
    print("RAG indexing complete.")

def process_rag_query(user_query: str, emotion: str, min_score: float = 0.2) -> Dict:
    """
    Process a user query through the RAG pipeline.
    Returns a dictionary with:
    - reply: The generated response
    - used_rag: Boolean whether context was injected
    - retrieved_chunks: The chunks retrieved and their scores
    """
    global _retriever
    if _retriever is None:
        print("RAG not initialized. Initializing now...")
        # Assume default directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        init_rag_system(os.path.join(base_dir, 'data', 'knowledge_base'))
        
    # Retrieve top K chunks
    top_chunks = _retriever.retrieve(user_query, top_k=3, min_score=min_score)
    
    # Build Prompt
    prompt = build_rag_prompt(user_query, emotion, top_chunks)
    
    # Get Gemini Response
    reply = ask_gemini(prompt)
    
    # Format metadata for logging/admin
    retrieved_data = []
    for doc, score in top_chunks:
        retrieved_data.append({
            'source': doc.get('metadata', {}).get('source', 'Unknown'),
            'score': float(score),
            'text': doc['text'][:100] + '...' # Truncate for logging
        })
        
    return {
        'reply': reply,
        'used_rag': len(top_chunks) > 0,
        'retrieved_chunks': retrieved_data
    }
