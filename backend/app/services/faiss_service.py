import logging
import numpy as np
import faiss
import pickle
import os
from typing import List, Tuple, Optional, Dict

logger = logging.getLogger(__name__)


class FAISSService:
    
    def __init__(self):
        self.index = None
        self.person_ids = []
        self.dimension = 512  # Facenet512 embedding dimension
        self.index_file = 'faiss_index.bin'
        self.mapping_file = 'faiss_mapping.pkl'
        self.is_initialized = False
        
    def initialize(self, config=None):
        """Initialize or load existing FAISS index"""
        try:
            # Try to load existing index
            if os.path.exists(self.index_file) and os.path.exists(self.mapping_file):
                self.load_index()
                logger.info("[FAISS] Loaded existing index")
            else:
                # Create new index
                self.create_index()
                logger.info("[FAISS] Created new index")
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"[FAISS] Initialization error: {e}")
            self.create_index()  # Fallback to new index
    
    def create_index(self):
        """Create a new FAISS index"""
        try:
            # Use IndexFlatIP for cosine similarity (after L2 normalization)
            # This is more accurate than Euclidean distance for face embeddings
            self.index = faiss.IndexFlatIP(self.dimension)
            self.person_ids = []
            logger.info(f"[FAISS] Created new index with dimension {self.dimension}")
            
        except Exception as e:
            logger.error(f"[FAISS] Index creation error: {e}")
            raise
    
    def add_person(self, person_id: int, embedding: np.ndarray) -> bool:
        """Add a person's embedding to the index"""
        try:
            if self.index is None:
                self.create_index()
            
            # Ensure embedding is correct shape and type
            if len(embedding) != self.dimension:
                logger.error(f"[FAISS] Invalid embedding dimension: {len(embedding)} != {self.dimension}")
                return False
            
            # Normalize embedding for cosine similarity
            embedding = embedding / np.linalg.norm(embedding)
            
            # Convert to float32 and reshape
            embedding = embedding.astype('float32').reshape(1, -1)
            
            # Add to index
            self.index.add(embedding)
            self.person_ids.append(person_id)
            
            logger.info(f"[FAISS] Added person {person_id}, total persons: {len(self.person_ids)}")
            
            # Save index periodically (every 10 additions)
            if len(self.person_ids) % 10 == 0:
                self.save_index()
            
            return True
            
        except Exception as e:
            logger.error(f"[FAISS] Error adding person {person_id}: {e}")
            return False
    
    def search(self, embedding: np.ndarray, k: int = 5, threshold: float = 0.6) -> List[Tuple[int, float]]:
        
        try:
            if self.index is None or len(self.person_ids) == 0:
                logger.warning("[FAISS] Index is empty")
                return []
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            # Convert to float32 and reshape
            embedding = embedding.astype('float32').reshape(1, -1)
            
            # Search
            k = min(k, len(self.person_ids))  # Don't search for more than we have
            distances, indices = self.index.search(embedding, k)
            
            # Convert distances to confidences (for cosine similarity, higher is better)
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                
                confidence = float(dist)  # Distance is actually similarity for IndexFlatIP
                
                # Filter by threshold
                if confidence >= (1 - threshold):  # Convert threshold to similarity
                    person_id = self.person_ids[idx]
                    results.append((person_id, confidence))
            
            logger.info(f"[FAISS] Search found {len(results)} matches above threshold")
            return results
            
        except Exception as e:
            logger.error(f"[FAISS] Search error: {e}")
            return []
    
    def update_person(self, person_id: int, new_embedding: np.ndarray) -> bool:
        """Update a person's embedding (rebuild index)"""
        try:
            # Remove and re-add (requires rebuild)
            if person_id in self.person_ids:
                self.rebuild_from_database()
                return True
            return False
            
        except Exception as e:
            logger.error(f"[FAISS] Update error: {e}")
            return False
    
    def remove_person(self, person_id: int) -> bool:
        """Remove a person from index (requires rebuild)"""
        try:
            if person_id in self.person_ids:
                self.rebuild_from_database()
                return True
            return False
            
        except Exception as e:
            logger.error(f"[FAISS] Remove error: {e}")
            return False
    
    def rebuild_from_database(self):
        """Rebuild FAISS index from database"""
        try:
            from app import db
            from app.models import Person
            
            logger.info("[FAISS] Rebuilding index from database...")
            
            # Create new index
            self.create_index()
            
            # Get all active persons
            persons = Person.query.filter_by(status='active').all()
            
            for person in persons:
                try:
                    # Deserialize embedding
                    embedding = pickle.loads(person.embedding)
                    
                    # Add to index
                    self.add_person(person.id, embedding)
                    
                except Exception as e:
                    logger.error(f"[FAISS] Error adding person {person.id}: {e}")
                    continue
            
            # Save the rebuilt index
            self.save_index()
            
            logger.info(f"[FAISS] Rebuild complete: {len(self.person_ids)} persons indexed")
            
        except Exception as e:
            logger.error(f"[FAISS] Rebuild error: {e}")
            raise
    
    def save_index(self):
        """Save FAISS index to disk"""
        try:
            if self.index is not None:
                # Save FAISS index
                faiss.write_index(self.index, self.index_file)
                
                # Save person ID mapping
                with open(self.mapping_file, 'wb') as f:
                    pickle.dump(self.person_ids, f)
                
                logger.info(f"[FAISS] Index saved: {len(self.person_ids)} persons")
                
        except Exception as e:
            logger.error(f"[FAISS] Save error: {e}")
    
    def load_index(self):
        """Load FAISS index from disk"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(self.index_file)
            
            # Load person ID mapping
            with open(self.mapping_file, 'rb') as f:
                self.person_ids = pickle.load(f)
            
            logger.info(f"[FAISS] Index loaded: {len(self.person_ids)} persons")
            
        except Exception as e:
            logger.error(f"[FAISS] Load error: {e}")
            raise
    
    def get_total_persons(self) -> int:
        """Get total number of persons in index"""
        return len(self.person_ids)
    
    def get_person_embedding(self, person_id: int) -> Optional[np.ndarray]:
        """Get embedding for a specific person"""
        try:
            if person_id not in self.person_ids:
                return None
            
            idx = self.person_ids.index(person_id)
            
            # Get vector from index
            embedding = self.index.reconstruct(idx)
            
            return embedding
            
        except Exception as e:
            logger.error(f"[FAISS] Get embedding error: {e}")
            return None
    
    def clear_index(self):
        """Clear the entire index"""
        try:
            self.create_index()
            self.save_index()
            logger.info("[FAISS] Index cleared")
            
        except Exception as e:
            logger.error(f"[FAISS] Clear error: {e}")


# Global instance
faiss_service = FAISSService()
