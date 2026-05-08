def rescale_bertscore_f1(raw_f1: float) -> float:
    rescaled = raw_f1 * 4.0 + 1.0
    return max(1.0, min(5.0, rescaled))

def score_to_label(rescaled: float) -> str:
    if rescaled >= 4.5:
        return "Excellent"
    elif rescaled >= 3.5:
        return "Very Good"
    elif rescaled >= 2.5:
        return "Good"
    elif rescaled >= 1.5:
        return "Fair"
    else:
        return "Poor"

def reciprocal_rank_fusion(results_list: list[list], k: int = 60) -> list:
    if not results_list:
        return []
    if len(results_list) == 1:
        return results_list[0]
    
    scores = {}
    for results in results_list:
        for rank, item in enumerate(results):
            key = str(item)
            scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
    
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [item for item, _ in sorted_items]