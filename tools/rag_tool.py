import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

# Target vector store directory
DB_PATH = "vector_store"
COLLECTION_NAME = "candidate_resumes"

class RAGTool:
    def __init__(self):
        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=DB_PATH)
        
        # Configure sentence-transformers/all-MiniLM-L6-v2 embeddings
        try:
            self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        except Exception as e:
            # Fallback warning if loading takes long
            print(f"[Warning] Error initializing embedding function: {e}")
            self.emb_fn = None
            
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.emb_fn
        )

    def index_resumes(self, resumes_dir: str) -> int:
        """Reads all txt resumes, generates embeddings, and indexes them in ChromaDB."""
        if not os.path.exists(resumes_dir):
            return 0
            
        files = [f for f in os.listdir(resumes_dir) if f.endswith(".txt")]
        if not files:
            return 0
            
        documents = []
        ids = []
        metadatas = []
        
        for file in files:
            filepath = os.path.join(resumes_dir, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Basic parsing to extract candidate name from first line if possible
            name = "Unknown"
            for line in content.splitlines():
                if line.lower().startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                    break
            
            documents.append(content)
            ids.append(file.replace(".txt", ""))
            metadatas.append({
                "filename": file,
                "name": name,
                "filepath": filepath
            })
            
        if documents:
            # Add to collection (upsert to handle re-runs cleanly)
            self.collection.upsert(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            
        return len(documents)

    def search_candidates(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Queries the vector database for the top matching candidates."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        candidates = []
        if not results or not results['ids'] or not results['ids'][0]:
            return candidates
            
        # Parse output
        ids = results['ids'][0]
        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        
        for idx in range(len(ids)):
            # Convert cosine distance to compatibility score (percentage match)
            # Typically distance is 0 to 2 for cosine distance in chromadb.
            # Convert to a human-friendly match score.
            distance = distances[idx]
            match_score = max(0, min(100, int((1.0 - (distance / 2.0)) * 100)))
            
            candidates.append({
                "id": ids[idx],
                "name": metadatas[idx].get("name", "Unknown"),
                "filename": metadatas[idx].get("filename", ""),
                "filepath": metadatas[idx].get("filepath", ""),
                "resume_text": documents[idx],
                "score": match_score,
                "distance": distance
            })
            
        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates
