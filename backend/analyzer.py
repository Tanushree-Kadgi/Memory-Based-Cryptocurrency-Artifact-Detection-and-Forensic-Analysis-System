"""
Advanced Risk Analysis Module for SeedTrace
Implements multi-artifact risk scoring with weighted confidence
"""
from typing import Dict, Any, List


def analyze(findings, keyword_found=False, additional_artifacts=None):
    """
    Advanced risk analysis with multi-artifact scoring
    
    Args:
        findings: Seed phrase findings from detector
        keyword_found: Whether keyword search found matches
        additional_artifacts: Dictionary of additional crypto artifacts
        
    Returns:
        Dictionary with risk assessment and analysis details
    """
    result = {}
    risk_score = 0
    
    # Initialize additional artifacts if not provided
    if additional_artifacts is None:
        additional_artifacts = {
            "bitcoin_addresses": [],
            "ethereum_addresses": [],
            "private_key_indicators": [],
            "transaction_hashes": [],
            "wallet_traces": []
        }
    
    # 1. Seed Phrase Analysis (CRITICAL - highest weight)
    max_conf = 0
    if findings:
        max_conf = max(f['confidence'] for f in findings)
        # High confidence seed phrases = CRITICAL risk
        if max_conf >= 0.90:
            risk_score += 50
        elif max_conf >= 0.70:
            risk_score += 40
        elif max_conf >= 0.50:
            risk_score += 30
    
    # 2. Bitcoin Addresses (HIGH - medium-high weight)
    btc_count = len(additional_artifacts.get("bitcoin_addresses", []))
    if btc_count > 0:
        risk_score += min(btc_count * 5, 30)  # Max 30 points for BTC addresses
    
    # 3. Ethereum Addresses (HIGH)
    eth_count = len(additional_artifacts.get("ethereum_addresses", []))
    if eth_count > 0:
        risk_score += min(eth_count * 5, 30)
    
    # 3b. Solana Addresses (HIGH)
    sol_count = len(additional_artifacts.get("solana_addresses", []))
    if sol_count > 0:
        risk_score += min(sol_count * 5, 30)
    
    # 4. Private Key Indicators (CRITICAL)
    pk_indicators = additional_artifacts.get("private_key_indicators", [])
    pk_critical = [p for p in pk_indicators if p.get("severity") == "critical"]
    pk_high = [p for p in pk_indicators if p.get("severity") == "high"]
    pk_count = len(pk_indicators)
    
    if pk_critical:
        risk_score += 40
    elif pk_high:
        risk_score += 25
    elif pk_count > 0:
        risk_score += min(pk_count * 3, 20)
    
    # 5. Wallet Traces (MEDIUM)
    wallet_count = len(additional_artifacts.get("wallet_traces", []))
    if wallet_count > 0:
        risk_score += min(wallet_count * 2, 15)
    
    # 6. Transaction Hashes (LOW)
    tx_count = len(additional_artifacts.get("transaction_hashes", []))
    if tx_count > 0:
        risk_score += min(tx_count * 1, 10)
    
    # 7. Keyword Matches (MEDIUM)
    if keyword_found:
        risk_score += 10
    
    # Final Risk determination
    if risk_score >= 60:
        risk = "critical"
        message = "CRITICAL: Multiple high-risk cryptocurrency artifacts detected (Seed Phrases/Private Keys)"
    elif risk_score >= 40:
        risk = "high"
        message = "HIGH: Significant cryptocurrency artifacts found (Addresses/Indicators)"
    elif risk_score >= 20:
        risk = "medium"
        message = "MEDIUM: Cryptocurrency activity traces detected"
    elif risk_score >= 5:
        risk = "low"
        message = "LOW: Minimal artifacts detected"
    else:
        risk = "none"
        message = "No significant cryptocurrency artifacts detected"
    
    result['risk'] = risk
    result['risk_score'] = min(risk_score, 100)
    result['message'] = message
    result['findings'] = findings
    result['keyword_found'] = keyword_found
    result['artifact_summary'] = {
        'seed_phrases': len(findings),
        'bitcoin_addresses': btc_count,
        'ethereum_addresses': eth_count,
        'solana_addresses': sol_count,
        'private_keys': pk_count,
        'wallet_traces': wallet_count,
        'transaction_hashes': tx_count,
        'total_artifacts': (len(findings) + btc_count + eth_count + sol_count + 
                           pk_count + wallet_count + tx_count)
    }
    result['additional_artifacts'] = additional_artifacts
    
    return result


def get_risk_color(risk: str) -> str:
    """Get color code for risk level"""
    colors = {
        "critical": "#dc2626",  # Red
        "high": "#f97316",      # Orange
        "medium": "#eab308",    # Yellow
        "low": "#22c55e",       # Green
        "none": "#6b7280"       # Gray
    }
    return colors.get(risk.lower(), "#6b7280")


def get_risk_description(risk: str) -> str:
    """Get detailed description for risk level"""
    descriptions = {
        "critical": "CRITICAL RISK: Immediate attention required. Potential exposure of seed phrases, private keys, or highly sensitive cryptocurrency data.",
        "high": "HIGH RISK: Significant cryptocurrency artifacts detected. Multiple wallet addresses or indicators suggest active cryptocurrency usage.",
        "medium": "MEDIUM RISK: Cryptocurrency-related traces or indicators found. May indicate past or present cryptocurrency activity.",
        "low": "LOW RISK: Minimal cryptocurrency artifacts detected. Limited exposure risk.",
        "none": "NO RISK: No significant cryptocurrency artifacts detected in the analyzed memory dump."
    }
    return descriptions.get(risk.lower(), "Unknown risk level")


if __name__ == "__main__":
    # Test the analyzer
    test_findings = [
        {"confidence": 0.95, "phrase": "test seed phrase..."}
    ]
    
    test_artifacts = {
        "bitcoin_addresses": [
            {"address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "confidence": 0.85}
        ],
        "ethereum_addresses": [],
        "private_key_indicators": [],
        "transaction_hashes": [],
        "wallet_traces": [
            {"wallet": "metamask", "confidence": 0.40}
        ]
    }
    
    result = analyze(test_findings, keyword_found=True, additional_artifacts=test_artifacts)
    print(f"Risk: {result['risk']}")
    print(f"Score: {result['risk_score']}")
    print(f"Message: {result['message']}")
    print(f"Artifact Summary: {result['artifact_summary']}")