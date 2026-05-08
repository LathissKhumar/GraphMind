from typing import List, Dict, Any
import numpy as np
from src.evaluation.bertscore_evaluator import BERTScoreEvaluator
from src.evaluation.rescaler import rescale_bertscore_f1, score_to_label


class SemanticMetrics:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.bert_evaluator = BERTScoreEvaluator()
        self.model_name = model_name
        self._sentence_transformer = None
    
    def _load_sentence_transformer(self):
        if self._sentence_transformer is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._sentence_transformer = SentenceTransformer(self.model_name)
            except ImportError:
                self._sentence_transformer = None
        return self._sentence_transformer
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        transformer = self._load_sentence_transformer()
        if transformer is None:
            raise RuntimeError("sentence-transformers not available")
        return transformer.encode(texts, convert_to_numpy=True)
    
    def _compute_cosine(self, cand_emb: np.ndarray, ref_emb: np.ndarray) -> float:
        dot_product = np.dot(cand_emb, ref_emb)
        norm1 = np.linalg.norm(cand_emb)
        norm2 = np.linalg.norm(ref_emb)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))
    
    def _compute_euclidean(self, cand_emb: np.ndarray, ref_emb: np.ndarray) -> float:
        return float(np.linalg.norm(cand_emb - ref_emb))
    
    def _compute_manhattan(self, cand_emb: np.ndarray, ref_emb: np.ndarray) -> float:
        return float(np.sum(np.abs(cand_emb - ref_emb)))
    
    def _compute_jaccard(self, cand_emb: np.ndarray, ref_emb: np.ndarray) -> float:
        bin1 = (cand_emb > 0).astype(int)
        bin2 = (ref_emb > 0).astype(int)
        intersection = np.sum(bin1 & bin2)
        union = np.sum(bin1 | bin2)
        if union == 0:
            return 0.0
        return float(intersection / union)
    
    def evaluate_pair(self, candidate: str, reference: str) -> Dict[str, Any]:
        bertscore_f1 = self.bert_evaluator.compute_single(candidate, reference)
        bertscore_rescaled = rescale_bertscore_f1(bertscore_f1)
        
        embeddings = self._get_embeddings([candidate, reference])
        cand_emb = embeddings[0]
        ref_emb = embeddings[1]
        
        cosine_sim = self._compute_cosine(cand_emb, ref_emb)
        euclidean_dist = self._compute_euclidean(cand_emb, ref_emb)
        manhattan_dist = self._compute_manhattan(cand_emb, ref_emb)
        jaccard_sim = self._compute_jaccard(cand_emb, ref_emb)
        
        return {
            'bertscore_f1': bertscore_f1,
            'bertscore_rescaled': bertscore_rescaled,
            'cosine_sim': cosine_sim,
            'euclidean_dist': euclidean_dist,
            'manhattan_dist': manhattan_dist,
            'jaccard_sim': jaccard_sim,
            'label': score_to_label(bertscore_rescaled)
        }
    
    def evaluate_batch(self, candidates: List[str], references: List[str]) -> List[Dict[str, Any]]:
        if len(candidates) != len(references):
            raise ValueError("Candidates and references must have the same length")
        
        results = []
        for candidate, reference in zip(candidates, references):
            results.append(self.evaluate_pair(candidate, reference))
        
        return results