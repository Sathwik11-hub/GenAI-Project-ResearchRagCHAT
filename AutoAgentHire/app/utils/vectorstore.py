"""
Vector store service for RAG embeddings and similarity search
"""

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from typing import List, Dict, Any, Optional, Tuple

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

import pickle
import os
from datetime import datetime

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class VectorStoreService:
    """Service for managing embeddings and similarity search"""
    
    def __init__(self):
        if settings.OPENAI_API_KEY and OPENAI_AVAILABLE:
            openai.api_key = settings.OPENAI_API_KEY
        elif not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available - embeddings will use dummy values")
        elif not NUMPY_AVAILABLE:
            logger.warning("NumPy not available - vector operations will be limited")
        
        self.embeddings_cache = {}
        self.documents = []
        self.embeddings_matrix = None
        self.cache_file = "embeddings_cache.pkl"
        
        # Load existing cache if available
        self._load_cache()
    
    async def generate_embedding(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """Generate embedding for given text"""
        
        try:
            # Check cache first
            cache_key = f"{model}:{hash(text)}"
            if cache_key in self.embeddings_cache:
                return self.embeddings_cache[cache_key]
            
            if not settings.OPENAI_API_KEY or not OPENAI_AVAILABLE:
                # Return dummy embedding if no API key
                logger.warning("No OpenAI API key provided or OpenAI not available, returning dummy embedding")
                return [0.0] * settings.VECTOR_DIMENSION
            
            # Generate embedding using OpenAI
            response = openai.Embedding.create(
                model=model,
                input=text
            )
            
            embedding = response['data'][0]['embedding']
            
            # Cache the embedding
            self.embeddings_cache[cache_key] = embedding
            self._save_cache()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return dummy embedding as fallback
            return [0.0] * settings.VECTOR_DIMENSION
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str], 
        model: str = "text-embedding-ada-002"
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for existing embeddings
        for i, text in enumerate(texts):
            cache_key = f"{model}:{hash(text)}"
            if cache_key in self.embeddings_cache:
                embeddings.append(self.embeddings_cache[cache_key])
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Generate embeddings for uncached texts
        if uncached_texts and settings.OPENAI_API_KEY and OPENAI_AVAILABLE:
            try:
                response = openai.Embedding.create(
                    model=model,
                    input=uncached_texts
                )
                
                # Update embeddings and cache
                for i, embedding_data in enumerate(response['data']):
                    embedding = embedding_data['embedding']
                    original_index = uncached_indices[i]
                    embeddings[original_index] = embedding
                    
                    # Cache the embedding
                    cache_key = f"{model}:{hash(uncached_texts[i])}"
                    self.embeddings_cache[cache_key] = embedding
                
                self._save_cache()
                
            except Exception as e:
                logger.error(f"Error generating batch embeddings: {str(e)}")
                # Fill missing embeddings with dummy values
                for i in uncached_indices:
                    if embeddings[i] is None:
                        embeddings[i] = [0.0] * settings.VECTOR_DIMENSION
        
        # Fill any remaining None values with dummy embeddings
        for i in range(len(embeddings)):
            if embeddings[i] is None:
                embeddings[i] = [0.0] * settings.VECTOR_DIMENSION
        
        return embeddings
    
    async def add_documents(
        self, 
        documents: List[Dict[str, Any]], 
        generate_embeddings: bool = True
    ):
        """Add documents to the vector store"""
        
        try:
            logger.info(f"Adding {len(documents)} documents to vector store")
            
            # Add documents to storage
            start_index = len(self.documents)
            self.documents.extend(documents)
            
            if generate_embeddings:
                # Extract text content for embedding
                texts = []
                for doc in documents:
                    if 'content' in doc:
                        texts.append(doc['content'])
                    elif 'text' in doc:
                        texts.append(doc['text'])
                    else:
                        texts.append(str(doc))
                
                # Generate embeddings
                embeddings = await self.generate_embeddings_batch(texts)
                
                # Update embeddings matrix
                if self.embeddings_matrix is None and NUMPY_AVAILABLE:
                    self.embeddings_matrix = np.array(embeddings)
                elif NUMPY_AVAILABLE:
                    self.embeddings_matrix = np.vstack([
                        self.embeddings_matrix,
                        np.array(embeddings)
                    ])
                else:
                    logger.warning("NumPy not available - embeddings matrix not updated")
                
                # Add embeddings to documents
                for i, doc in enumerate(documents):
                    doc['embedding'] = embeddings[i]
                    doc['index'] = start_index + i
            
            logger.info(f"Successfully added {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        score_threshold: float = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar documents using cosine similarity"""
        
        try:
            if not self.documents:
                logger.warning("No documents in vector store")
                return []
            
            if not NUMPY_AVAILABLE:
                logger.warning("NumPy not available - cannot perform similarity search")
                return []
            
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            if self.embeddings_matrix is None:
                logger.warning("No embeddings matrix available")
                return []
            
            # Calculate similarities
            query_vector = np.array(query_embedding).reshape(1, -1)
            
            if SKLEARN_AVAILABLE:
                similarities = cosine_similarity(query_vector, self.embeddings_matrix)[0]
            else:
                # Simple dot product similarity as fallback
                similarities = []
                for i in range(len(self.embeddings_matrix)):
                    doc_vector = self.embeddings_matrix[i]
                    similarity = np.dot(query_vector[0], doc_vector) / (np.linalg.norm(query_vector[0]) * np.linalg.norm(doc_vector))
                    similarities.append(similarity)
                similarities = np.array(similarities)
            
            # Get top k similar documents
            top_indices = np.argsort(similarities)[::-1][:k]
            
            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                
                # Apply score threshold if specified
                if score_threshold and score < score_threshold:
                    continue
                
                document = self.documents[idx].copy()
                # Remove embedding from result to save space
                if 'embedding' in document:
                    del document['embedding']
                
                results.append((document, score))
            
            logger.info(f"Found {len(results)} similar documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    async def semantic_search_jobs(
        self, 
        user_profile_text: str, 
        job_documents: List[Dict[str, Any]], 
        k: int = 10
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Semantic search specifically for job matching"""
        
        try:
            # Temporarily add job documents
            original_count = len(self.documents)
            await self.add_documents(job_documents)
            
            # Perform search
            results = await self.similarity_search(user_profile_text, k=k)
            
            # Remove temporary documents
            self.documents = self.documents[:original_count]
            if self.embeddings_matrix is not None and len(job_documents) > 0:
                self.embeddings_matrix = self.embeddings_matrix[:original_count]
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic job search: {str(e)}")
            return []
    
    def calculate_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """Calculate cosine similarity between two embeddings"""
        
        try:
            if not SKLEARN_AVAILABLE and not NUMPY_AVAILABLE:
                # Very simple similarity as fallback
                return 0.5
            elif not SKLEARN_AVAILABLE and NUMPY_AVAILABLE:
                # Simple dot product similarity as fallback
                vec1 = np.array(embedding1)
                vec2 = np.array(embedding2)
                return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
            
            vec1 = np.array(embedding1).reshape(1, -1)
            vec2 = np.array(embedding2).reshape(1, -1)
            
            similarity = cosine_similarity(vec1, vec2)[0][0]
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    async def find_similar_resumes(
        self, 
        target_resume: Dict[str, Any], 
        resume_database: List[Dict[str, Any]], 
        k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Find similar resumes from a database"""
        
        try:
            # Generate embedding for target resume
            target_text = self._extract_resume_text(target_resume)
            target_embedding = await self.generate_embedding(target_text)
            
            # Generate embeddings for resume database
            resume_texts = [self._extract_resume_text(resume) for resume in resume_database]
            resume_embeddings = await self.generate_embeddings_batch(resume_texts)
            
            # Calculate similarities
            similarities = []
            for i, resume_embedding in enumerate(resume_embeddings):
                similarity = self.calculate_similarity(target_embedding, resume_embedding)
                similarities.append((resume_database[i], similarity))
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:k]
            
        except Exception as e:
            logger.error(f"Error finding similar resumes: {str(e)}")
            return []
    
    def _extract_resume_text(self, resume: Dict[str, Any]) -> str:
        """Extract text content from resume for embedding"""
        
        text_parts = []
        
        # Add summary
        if resume.get("summary"):
            text_parts.append(resume["summary"])
        
        # Add skills
        if resume.get("skills"):
            text_parts.append("Skills: " + ", ".join(resume["skills"]))
        
        # Add experience
        for exp in resume.get("experience", []):
            if exp.get("description"):
                text_parts.append(exp["description"])
            if exp.get("title"):
                text_parts.append(exp["title"])
        
        # Add education
        for edu in resume.get("education", []):
            if edu.get("degree"):
                text_parts.append(edu["degree"])
        
        return " ".join(text_parts)
    
    def _load_cache(self):
        """Load embeddings cache from file"""
        
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
                logger.info(f"Loaded {len(self.embeddings_cache)} cached embeddings")
            
        except Exception as e:
            logger.warning(f"Could not load embeddings cache: {str(e)}")
            self.embeddings_cache = {}
    
    def _save_cache(self):
        """Save embeddings cache to file"""
        
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
            
        except Exception as e:
            logger.warning(f"Could not save embeddings cache: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        
        return {
            "document_count": len(self.documents),
            "embeddings_cached": len(self.embeddings_cache),
            "embeddings_matrix_shape": self.embeddings_matrix.shape if self.embeddings_matrix is not None else None,
            "cache_file_exists": os.path.exists(self.cache_file),
            "vector_dimension": settings.VECTOR_DIMENSION
        }
    
    def clear_cache(self):
        """Clear the embeddings cache"""
        
        self.embeddings_cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        logger.info("Embeddings cache cleared")
    
    def clear_documents(self):
        """Clear all documents and embeddings"""
        
        self.documents = []
        self.embeddings_matrix = None
        logger.info("Documents and embeddings cleared")