from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split a long text into smaller chunks of approximately `chunk_size` characters,
    with an overlap of `overlap` characters.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        
        # If not at the end, try to find a natural break point (newline or space)
        if end < text_length:
            # Try to find a newline within the last 50 chars of the chunk
            newline_idx = text.rfind('\n', max(start, end - 50), end)
            if newline_idx != -1:
                end = newline_idx + 1
            else:
                # Try to find a space within the last 20 chars
                space_idx = text.rfind(' ', max(start, end - 20), end)
                if space_idx != -1:
                    end = space_idx + 1
                    
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            
        start = end - overlap
        if start < 0:
            start = 0
            
    return chunks

def process_documents(documents: List[Dict], chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """
    Process a list of documents into chunks, preserving metadata.
    """
    chunked_docs = []
    
    for doc in documents:
        text = doc.get('text', '')
        metadata = doc.get('metadata', {})
        
        chunks = chunk_text(text, chunk_size, overlap)
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_index'] = i
            
            chunked_docs.append({
                'text': chunk,
                'metadata': chunk_metadata
            })
            
    return chunked_docs
