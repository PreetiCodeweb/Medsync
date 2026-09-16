"""
Professional RAG (Retrieval-Augmented Generation) System for MedSync
Implements vector search, document processing, and intelligent retrieval
"""
import logging
from typing import List, Dict, Optional, Any
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings
import numpy as np
from pathlib import Path
import json
import hashlib
from datetime import datetime

from config import settings

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class RAGSystem:
    """
    Professional RAG System with vector embeddings and ChromaDB
    """
    
    def __init__(self):
        """Initialize the RAG system with configuration"""
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.top_k_results = settings.TOP_K_RESULTS
        
        if settings.ENABLE_RAG:
            self._initialize_system()
        else:
            logger.warning("RAG system is disabled in configuration")
    
    def _initialize_system(self):
        """Initialize embedding model and vector database"""
        try:
            logger.info("Initializing RAG system...")
            
            # Initialize embedding model
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            
            # Initialize ChromaDB
            logger.info(f"Initializing ChromaDB with persist directory: {settings.CHROMA_PERSIST_DIRECTORY}")
            self.chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="medical_knowledge",
                metadata={"description": "Medical knowledge base for symptom analysis"}
            )
            
            logger.info("RAG system initialized successfully")
            
            # Load initial medical knowledge if collection is empty
            if self.collection.count() == 0:
                logger.info("Loading initial medical knowledge base...")
                self._load_medical_knowledge()
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {str(e)}")
            raise
    
    def _load_medical_knowledge(self):
        """Load initial medical knowledge into the vector database"""
        medical_documents = self._get_medical_documents()
        
        for doc in medical_documents:
            self.add_document(
                content=doc['content'],
                metadata=doc['metadata'],
                doc_id=doc['id']
            )
        
        logger.info(f"Loaded {len(medical_documents)} medical documents into knowledge base")
    
    def _get_medical_documents(self) -> List[Dict]:
        """
        Get initial medical documents for the knowledge base
        In production, this would load from external sources/files
        """
        return [
            {
                "id": "cardio_001",
                "content": """
                Cardiovascular System Diseases: Heart conditions include coronary artery disease, 
                heart attack, heart failure, arrhythmias, and heart valve problems. Common symptoms 
                include chest pain, shortness of breath, fatigue, and palpitations. Risk factors 
                include high blood pressure, high cholesterol, smoking, diabetes, and family history. 
                Diagnosis involves ECG, echocardiogram, stress tests, and cardiac catheterization.
                Treatment ranges from lifestyle changes and medications to surgical interventions.
                """,
                "metadata": {
                    "category": "cardiology",
                    "specialty": "cardiology",
                    "severity": "high",
                    "keywords": "heart, chest pain, cardiac, cardiovascular"
                }
            },
            {
                "id": "neuro_001",
                "content": """
                Neurological Disorders: Conditions affecting the brain and nervous system include 
                stroke, migraine, epilepsy, Parkinson's disease, multiple sclerosis, and Alzheimer's. 
                Symptoms vary widely but may include headaches, seizures, memory loss, movement 
                disorders, and cognitive decline. Risk factors include age, genetics, head trauma, 
                and cardiovascular disease. Diagnosis involves neurological exams, imaging (MRI, CT), 
                and specialized tests. Treatment includes medications, therapy, and sometimes surgery.
                """,
                "metadata": {
                    "category": "neurology",
                    "specialty": "neurology",
                    "severity": "medium",
                    "keywords": "brain, headache, neurological, stroke, migraine"
                }
            },
            {
                "id": "resp_001",
                "content": """
                Respiratory System: Conditions include asthma, COPD, pneumonia, bronchitis, 
                tuberculosis, and lung cancer. Common symptoms are cough, shortness of breath, 
                wheezing, chest tightness, and fatigue. Risk factors include smoking, pollution, 
                occupational exposures, and genetics. Diagnosis involves pulmonary function tests, 
                chest X-rays, CT scans, and bronchoscopy. Treatment includes bronchodilators, 
                corticosteroids, antibiotics, and oxygen therapy.
                """,
                "metadata": {
                    "category": "pulmonology",
                    "specialty": "pulmonology",
                    "severity": "medium",
                    "keywords": "lungs, breathing, respiratory, asthma, cough"
                }
            },
            {
                "id": "gastro_001",
                "content": """
                Gastrointestinal Disorders: Include GERD, IBS, IBD, ulcers, gallstones, 
                and liver disease. Symptoms involve abdominal pain, nausea, vomiting, 
                diarrhea, constipation, and digestive issues. Risk factors include diet, 
                stress, infections, medications, and genetics. Diagnosis involves endoscopy, 
                colonoscopy, imaging, and lab tests. Treatment includes dietary changes, 
                medications, and sometimes surgery.
                """,
                "metadata": {
                    "category": "gastroenterology",
                    "specialty": "gastroenterology",
                    "severity": "low",
                    "keywords": "stomach, digestive, gastrointestinal, abdominal"
                }
            },
            {
                "id": "ortho_001",
                "content": """
                Orthopedic Conditions: Include arthritis, fractures, sprains, tendonitis, 
                back pain, and sports injuries. Symptoms involve pain, swelling, limited 
                movement, and joint stiffness. Risk factors include age, overuse, trauma, 
                obesity, and genetics. Diagnosis involves physical examination, X-rays, 
                MRI, and CT scans. Treatment includes rest, physical therapy, medications, 
                injections, and surgery.
                """,
                "metadata": {
                    "category": "orthopedics",
                    "specialty": "orthopedics",
                    "severity": "medium",
                    "keywords": "bones, joints, fracture, arthritis, musculoskeletal"
                }
            },
            {
                "id": "emergency_001",
                "content": """
                Emergency Medical Conditions: Life-threatening situations include heart attack, 
                stroke, severe bleeding, difficulty breathing, severe burns, head trauma, 
                anaphylaxis, and poisoning. Immediate symptoms may include chest pain, 
                confusion, unconsciousness, severe pain, and difficulty breathing. These require 
                immediate emergency medical attention. Call emergency services immediately. 
                Time is critical in emergency situations.
                """,
                "metadata": {
                    "category": "emergency",
                    "specialty": "emergency_medicine",
                    "severity": "critical",
                    "keywords": "emergency, critical, life-threatening, urgent"
                }
            },
            {
                "id": "pediatrics_001",
                "content": """
                Pediatric Conditions: Children's medical issues include asthma, allergies, 
                infections, developmental disorders, and injuries. Symptoms may be different 
                from adults and require specialized care. Common conditions include ear 
                infections, strep throat, asthma, ADHD, and autism. Pediatric care focuses 
                on growth, development, and age-appropriate treatments.
                """,
                "metadata": {
                    "category": "pediatrics",
                    "specialty": "pediatrics",
                    "severity": "low",
                    "keywords": "children, pediatric, child, developmental"
                }
            },
            {
                "id": "dermatology_001",
                "content": """
                Skin Conditions: Include acne, eczema, psoriasis, dermatitis, skin 
                infections, and skin cancer. Symptoms involve rashes, itching, redness, 
                swelling, and changes in skin appearance. Risk factors include genetics, 
                environment, allergies, and immune system. Diagnosis involves physical 
                examination, biopsies, and allergy tests. Treatment includes topical 
                medications, oral medications, and lifestyle changes.
                """,
                "metadata": {
                    "category": "dermatology",
                    "specialty": "dermatology",
                    "severity": "low",
                    "keywords": "skin, rash, dermatology, acne, eczema"
                }
            }
        ]
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks for better embedding
        """
        chunks = []
        text_length = len(text)
        
        for i in range(0, text_length, self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def add_document(self, content: str, metadata: Dict[str, Any], doc_id: Optional[str] = None):
        """
        Add a document to the knowledge base
        """
        if not settings.ENABLE_RAG:
            logger.warning("RAG system is disabled")
            return None
        
        try:
            # Generate document ID if not provided
            if doc_id is None:
                doc_id = hashlib.md5(content.encode()).hexdigest()
            
            # Chunk the document
            chunks = self._chunk_text(content)
            
            # Generate embeddings for chunks
            embeddings = self.embedding_model.encode(chunks).tolist()
            
            # Add to ChromaDB
            ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            metadatas = [{**metadata, "chunk_index": i} for i in range(len(chunks))]
            
            self.collection.add(
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added document {doc_id} with {len(chunks)} chunks to knowledge base")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise
    
    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant information
        """
        if not settings.ENABLE_RAG:
            logger.warning("RAG system is disabled")
            return []
        
        try:
            top_k = top_k or self.top_k_results
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "similarity_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                    "relevance": self._calculate_relevance(1 - results['distances'][0][i])
                })
            
            logger.info(f"Found {len(formatted_results)} results for query: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            raise
    
    def _calculate_relevance(self, similarity_score: float) -> str:
        """
        Calculate relevance category based on similarity score
        """
        if similarity_score >= 0.8:
            return "high"
        elif similarity_score >= 0.6:
            return "medium"
        else:
            return "low"
    
    def analyze_symptoms(self, symptoms: str) -> Dict[str, Any]:
        """
        Analyze symptoms using RAG system
        """
        if not settings.ENABLE_RAG:
            logger.warning("RAG system is disabled, using fallback analysis")
            return self._fallback_analysis(symptoms)
        
        try:
            # Search for relevant medical information
            search_results = self.search(symptoms, top_k=3)
            
            if not search_results:
                return self._fallback_analysis(symptoms)
            
            # Analyze results
            categories = {}
            specialties = set()
            severity_scores = []
            
            # Check for emergency keywords in original symptoms
            emergency_keywords = ['severe', 'emergency', 'critical', 'unconscious', 'fainting', 'cannot breathe', 'extreme pain']
            has_emergency_keywords = any(keyword in symptoms.lower() for keyword in emergency_keywords)
            
            for result in search_results:
                category = result['metadata'].get('category', 'general')
                specialty = result['metadata'].get('specialty', 'general_medicine')
                severity = result['metadata'].get('severity', 'low')
                
                categories[category] = categories.get(category, 0) + result['similarity_score']
                specialties.add(specialty)
                
                # Convert severity to numeric score with weight
                severity_mapping = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
                # Boost emergency cases significantly
                severity_weight = 5.0 if category == 'emergency' else 1.0
                # Boost cardiology for chest-related symptoms
                if category == 'cardiology' and any(word in symptoms.lower() for word in ['chest', 'heart']):
                    severity_weight = 3.0
                severity_scores.append(severity_mapping.get(severity, 1) * result['similarity_score'] * severity_weight)
            
            # Override to critical if emergency keywords present
            if has_emergency_keywords:
                severity_level = "critical"
                best_category = "emergency"
                best_specialty = "emergency_medicine"
            else:
                # Determine best category and specialty
                best_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "general"
                best_specialty = list(specialties)[0] if specialties else "general_medicine"
                
                # Calculate overall severity with more sensitive thresholds
                avg_severity = sum(severity_scores) / len(severity_scores) if severity_scores else 1
                if avg_severity >= 2.5:
                    severity_level = "critical"
                elif avg_severity >= 1.8:
                    severity_level = "high"
                elif avg_severity >= 1.2:
                    severity_level = "medium"
                else:
                    severity_level = "low"
            
            # Generate recommendation
            recommendation = self._generate_recommendation(best_category, severity_level, search_results)
            
            # Extract possible conditions from keywords
            possible_conditions = []
            for result in search_results[:2]:
                keywords = result['metadata'].get('keywords', 'general')
                if isinstance(keywords, str):
                    possible_conditions.append(keywords.split(',')[0].strip())
                else:
                    possible_conditions.append('general')
            
            return {
                "possible_conditions": possible_conditions,
                "recommended_department": best_specialty,
                "category": best_category,
                "severity": severity_level,
                "recommendation": recommendation,
                "confidence": max(result['similarity_score'] for result in search_results) if search_results else 0.5,
                "rag_enabled": True,
                "sources": [result['id'] for result in search_results]
            }
            
        except Exception as e:
            logger.error(f"Error in symptom analysis: {str(e)}")
            return self._fallback_analysis(symptoms)
    
    def _generate_recommendation(self, category: str, severity: str, search_results: List[Dict]) -> str:
        """
        Generate appropriate recommendation based on analysis
        """
        if severity == "critical":
            return "🚨 CRITICAL: Immediate emergency medical attention required. Call emergency services (911) or go to nearest emergency department immediately."
        elif severity == "high":
            return "⚠️ HIGH PRIORITY: Immediate medical attention recommended. Please visit emergency department or urgent care facility as soon as possible."
        elif severity == "medium":
            return f"📋 CONSULTATION: Consult with {category} specialist recommended for proper evaluation and treatment within 24-48 hours."
        else:
            return "📅 ROUTINE: Schedule appointment with healthcare provider for proper diagnosis. Monitor symptoms and seek care if they worsen."
    
    def _fallback_analysis(self, symptoms: str) -> Dict[str, Any]:
        """
        Fallback analysis when RAG system is disabled
        """
        symptoms_lower = symptoms.lower()
        
        analysis_result = {
            "possible_conditions": ["General condition"],
            "recommended_department": "General Medicine",
            "category": "general",
            "severity": "low",
            "recommendation": "Please consult with a healthcare professional for proper diagnosis.",
            "confidence": 0.3,
            "rag_enabled": False,
            "sources": []
        }
        
        # Check for emergency indicators
        emergency_keywords = ['severe', 'emergency', 'critical', 'unconscious', 'fainting', 'cannot breathe', 'extreme pain']
        has_emergency = any(keyword in symptoms_lower for keyword in emergency_keywords)
        
        if has_emergency:
            analysis_result.update({
                "possible_conditions": ["Potential emergency condition"],
                "recommended_department": "Emergency Medicine",
                "category": "emergency",
                "severity": "critical",
                "recommendation": "🚨 CRITICAL: Immediate emergency medical attention required. Call emergency services (911) or go to nearest emergency department immediately."
            })
        elif any(word in symptoms_lower for word in ['chest', 'heart', 'breath']):
            # Check severity of chest symptoms
            chest_severity = 'high' if any(word in symptoms_lower for word in ['severe', 'extreme', 'cannot']) else 'medium'
            analysis_result.update({
                "possible_conditions": ["cardiac issue", "respiratory problem"],
                "recommended_department": "Cardiology",
                "category": "cardiology",
                "severity": chest_severity,
                "recommendation": "⚠️ HIGH PRIORITY: Immediate medical attention recommended. Please visit emergency department or urgent care facility as soon as possible." if chest_severity == 'high' else "📋 CONSULTATION: Consult with cardiology specialist recommended for proper evaluation."
            })
        
        elif any(word in symptoms_lower for word in ['head', 'migraine', 'dizzy']):
            analysis_result.update({
                "possible_conditions": ["migraine", "neurological issue"],
                "recommended_department": "Neurology",
                "category": "neurology",
                "severity": "medium",
                "recommendation": "📋 CONSULTATION: Consult with neurologist for proper evaluation."
            })
        
        elif any(word in symptoms_lower for word in ['bone', 'joint', 'muscle', 'fracture']):
            analysis_result.update({
                "possible_conditions": ["musculoskeletal injury", "fracture"],
                "recommended_department": "Orthopedics",
                "category": "orthopedics",
                "severity": "medium",
                "recommendation": "📋 CONSULTATION: Orthopedic consultation recommended for proper diagnosis and treatment."
            })
        
        return analysis_result
        
        return analysis_result
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base
        """
        if not settings.ENABLE_RAG:
            return {"rag_enabled": False}
        
        try:
            return {
                "rag_enabled": True,
                "total_documents": self.collection.count(),
                "embedding_model": settings.EMBEDDING_MODEL,
                "chunk_size": self.chunk_size,
                "top_k_results": self.top_k_results
            }
        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {str(e)}")
            return {"rag_enabled": True, "error": str(e)}
    
    def reset_knowledge_base(self):
        """
        Reset the knowledge base (use with caution)
        """
        if not settings.ENABLE_RAG:
            logger.warning("RAG system is disabled")
            return
        
        try:
            self.chroma_client.delete_collection("medical_knowledge")
            self.collection = self.chroma_client.create_collection(
                name="medical_knowledge",
                metadata={"description": "Medical knowledge base for symptom analysis"}
            )
            self._load_medical_knowledge()
            logger.info("Knowledge base reset successfully")
        except Exception as e:
            logger.error(f"Error resetting knowledge base: {str(e)}")
            raise


# Global RAG system instance
rag_system = RAGSystem()