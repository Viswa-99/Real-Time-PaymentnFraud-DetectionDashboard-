import math
from typing import List, Dict, Any
from .schemas import Reason


def generate_reasons(
    feature_dict: Dict[str, Any],
    layer1_score: float,
    risk_probability: float,
    layer1_threshold: float = 0.51356
) -> List[Reason]:
    """
    Generate human-readable reasons for fraud/anomaly risk based on actual transaction features.
    Does NOT use synthetic anomaly_type label.
    """
    candidates = []

    amount = float(feature_dict.get("amount", 0.0))
    amount_ratio = float(feature_dict.get("recent_amount_ratio", 0.0))
    amount_z = float(feature_dict.get("amount_zscore", 0.0))
    user_avg = float(feature_dict.get("user_avg_amount", 0.0))
    is_new_receiver = int(feature_dict.get("is_new_receiver", 0))
    is_new_device = int(feature_dict.get("is_new_device", 0))
    distance = float(feature_dict.get("distance_from_usual_location", 0.0))
    tx_1h = int(feature_dict.get("transactions_last_1hour", 0))
    new_m15 = int(feature_dict.get("new_merchants_last_15min", 0))
    new_m1h = int(feature_dict.get("new_merchants_last_1hour", 0))

    # Priority 5: High severity amount ratios / z-scores / location drift / new merchants
    if math.isfinite(amount_ratio) and amount_ratio >= 3.0:
        candidates.append((
            5,
            "Amount significantly above recent behavior",
            f"Transaction amount is {amount_ratio:.1f}x the user's recent average."
        ))
    elif math.isfinite(amount_ratio) and amount_ratio >= 2.0:
        candidates.append((
            3,
            "Amount above recent behavior",
            f"Transaction amount is {amount_ratio:.1f}x the user's recent average."
        ))

    if math.isfinite(amount_z) and amount_z >= 3.0:
        candidates.append((
            5,
            "Strong amount deviation",
            "Transaction amount strongly deviates from the user's historical behavior."
        ))

    if distance >= 200.0:
        candidates.append((
            5,
            "Unusual transaction location",
            f"Transaction is approximately {distance:,.0f} km from the user's usual location."
        ))

    if new_m15 >= 2:
        candidates.append((
            5,
            "Multiple new merchants recently",
            f"{new_m15} new merchant interactions occurred in the previous 15 minutes."
        ))
    elif new_m1h >= 3:
        candidates.append((
            3,
            "Several new merchant interactions",
            f"{new_m1h} new merchant interactions occurred in the previous hour."
        ))

    # Priority 4: Structural novelty / velocity signals
    if is_new_receiver == 1:
        candidates.append((
            4,
            "New receiver detected",
            "This receiver has not previously appeared in the user's transaction history."
        ))

    if is_new_device == 1:
        candidates.append((
            4,
            "New device detected",
            "The transaction is associated with a device not previously used by this user."
        ))

    if tx_1h >= 5:
        candidates.append((
            4,
            "High transaction velocity",
            f"{tx_1h} transactions occurred in the previous hour."
        ))
    elif tx_1h >= 3:
        candidates.append((
            2,
            "Elevated transaction velocity",
            f"{tx_1h} transactions occurred in the previous hour."
        ))

    # Priority 3: Baseline Layer 1 score trigger
    if layer1_score >= layer1_threshold:
        candidates.append((
            3,
            "Unusual overall transaction behavior",
            f"Layer 1 anomaly score is {layer1_score:.3f}, above the baseline threshold."
        ))

    # Fallback if no specific condition met but elevated risk
    if not candidates:
        candidates.append((
            1,
            "Model-detected behavioral risk",
            "The combined transaction features indicate elevated risk."
        ))

    # Sort candidates by priority descending
    candidates.sort(key=lambda x: x[0], reverse=True)

    # Return top 3 to 4 reasons formatted as Reason objects
    top_reasons = candidates[:4]
    return [Reason(title=title, detail=detail) for _, title, detail in top_reasons]
