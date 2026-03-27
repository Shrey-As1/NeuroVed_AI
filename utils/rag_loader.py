import os
import json
import csv
import pandas as pd
from typing import List, Dict

def load_documents(directory: str) -> List[Dict]:
    """
    Load documents from the knowledge base directory.
    Supports .txt, .md, .csv, and .json files.
    Returns a list of dictionaries with 'text' and 'metadata'.
    """
    documents = []
    
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist. Creating it.")
        os.makedirs(directory)
        return documents

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
            
        ext = os.path.splitext(filename)[1].lower()
        
        try:
            if ext in ['.txt', '.md']:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        documents.append({
                            'text': content,
                            'metadata': {'source': filename, 'type': 'text'}
                        })
            
            elif ext == '.csv':
                df = pd.read_csv(filepath)
                # Look for question/answer or text columns
                text_cols = []
                for col in df.columns:
                    col_lower = str(col).lower()
                    if any(kw in col_lower for kw in ['text', 'content', 'answer', 'question', 'response']):
                        text_cols.append(col)
                
                if text_cols:
                    for i, row in df.iterrows():
                        content = " ".join([f"{col}: {row[col]}" for col in text_cols if pd.notna(row[col])])
                        if content.strip():
                            documents.append({
                                'text': content,
                                'metadata': {'source': filename, 'row': i, 'type': 'csv'}
                            })
                            
            elif ext == '.json':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for i, item in enumerate(data):
                            if isinstance(item, dict):
                                content = " ".join([f"{k}: {v}" for k, v in item.items() if isinstance(v, str)])
                            else:
                                content = str(item)
                                
                            if content.strip():
                                documents.append({
                                    'text': content,
                                    'metadata': {'source': filename, 'index': i, 'type': 'json'}
                                })
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            
    return documents
