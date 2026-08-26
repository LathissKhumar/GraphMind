from typing import List, Dict
import numpy as np


class BERTScoreEvaluator:
    def __init__(self, model_type: str = "bert-base-uncased"):
        self.model_type = model_type
        self._bert_score = None
        self._sentence_transformer = None
        
    def _load_bert_score(self):
        if self._bert_score is None:
            try:
                import bert_score
                self._bert_score = bert_score
            except ImportError:
                self._bert_score = None
        return self._bert_score
    
    def _load_sentence_transformer(self):
        if self._sentence_transformer is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                self._sentence_transformer = None
        return self._sentence_transformer
    
    def compute_f1(self, candidates: List[str], references: List[str]) -> Dict[str, float]:
        if len(candidates) != len(references):
            raise ValueError("Candidates and references must have the same length")
            
        bert_score = self._load_bert_score()
        
        if bert_score is not None:
            try:
                P, R, F1 = bert_score.score(
                    candidates, references, 
                    model_type=self.model_type,
                    verbose=False
                )
                return {
                    'precision': float(P.mean()),
                    'recall': float(R.mean()),
                    'f1': float(F1.mean())
                }
            except Exception:
                pass
        
        transformer = self._load_sentence_transformer()
        if transformer is None:
            raise RuntimeError(
                "Neither bert_score nor sentence_transformers is available. "
                "Install with: pip install bert-score sentence-transformers"
            )
        
        candidate_embeddings = transformer.encode(candidates, convert_to_tensor=True)
        reference_embeddings = transformer.encode(references, convert_to_tensor=True)
        
        similarities = []
        for i in range(len(candidates)):
            sim = np.dot(
                candidate_embeddings[i].cpu().numpy(),
                reference_embeddings[i].cpu().numpy()
            )
            similarities.append(float(sim))
        
        avg_sim = np.mean(similarities)
        return {
            'precision': avg_sim,
            'recall': avg_sim,
            'f1': avg_sim
        }
    
    def compute_single(self, candidate: str, reference: str) -> float:
        result = self.compute_f1([candidate], [reference])
        return result['f1']