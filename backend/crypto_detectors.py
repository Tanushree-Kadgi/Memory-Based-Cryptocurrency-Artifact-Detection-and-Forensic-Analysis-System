"""
Advanced Cryptocurrency Artifact Detection Module
Detects Bitcoin addresses, Ethereum addresses, Solana addresses, private keys, and wallet traces
"""
import re
import hashlib
import math
from typing import List, Dict, Any, Tuple


class ValidationUtils:
    """Utility class for cryptographic validation"""
    
    @staticmethod
    def base58_decode(s: str) -> bytes:
        """Decode a base58 string"""
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        try:
            n = 0
            for char in s:
                n = n * 58 + alphabet.index(char)
            
            res = bytearray()
            while n > 0:
                n, r = divmod(n, 256)
                res.append(r)
            
            for char in s:
                if char == alphabet[0]:
                    res.append(0)
                else:
                    break
            return bytes(res[::-1])
        except Exception:
            return b""

    @staticmethod
    def validate_btc_checksum(address: str) -> bool:
        """Validate Bitcoin legacy address checksum (Base58Check)"""
        try:
            if not (26 <= len(address) <= 35):
                return False
            decoded = ValidationUtils.base58_decode(address)
            if len(decoded) < 4:
                return False
            payload = decoded[:-4]
            checksum = decoded[-4:]
            h1 = hashlib.sha256(payload).digest()
            h2 = hashlib.sha256(h1).digest()
            return h2[:4] == checksum
        except Exception:
            return False

    @staticmethod
    def calculate_entropy(data: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not data:
            return 0.0
        prob = [float(data.count(c)) / len(data) for c in dict.fromkeys(list(data))]
        entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
        return entropy


class BitcoinAddressDetector:
    """Detects Bitcoin addresses in memory dumps with validation"""
    
    LEGACY_PATTERN = r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
    BECH32_PATTERN = r'\bbc1[a-zA-Z0-9]{11,71}\b'
    
    def __init__(self):
        self.legacy_regex = re.compile(self.LEGACY_PATTERN)
        self.bech32_regex = re.compile(self.BECH32_PATTERN)
    
    def detect(self, strings: List[Tuple[str, int]]) -> List[Dict[str, Any]]:
        findings = []
        for s, offset in strings:
            # Legacy addresses
            for match in self.legacy_regex.finditer(s):
                addr = match.group()
                is_valid = ValidationUtils.validate_btc_checksum(addr)
                if is_valid or len(addr) > 30:
                    findings.append({
                        "type": "BITCOIN_ADDRESS_LEGACY",
                        "address": addr,
                        "offset": offset + match.start(),
                        "confidence": 0.98 if is_valid else 0.65,
                        "checksum_valid": is_valid,
                        "network": "Mainnet" if addr.startswith('1') else "P2SH"
                    })
            
            # Bech32 addresses
            for match in self.bech32_regex.finditer(s):
                addr = match.group()
                findings.append({
                    "type": "BITCOIN_ADDRESS_BECH32",
                    "address": addr,
                    "offset": offset + match.start(),
                    "confidence": 0.90,
                    "network": "Bech32 (SegWit)"
                })
        return findings


class EthereumAddressDetector:
    """Detects Ethereum addresses with EIP-55 validation"""
    
    ETH_PATTERN = r'\b0x[a-fA-F0-9]{40}\b'
    
    def __init__(self):
        self.regex = re.compile(self.ETH_PATTERN)
    
    def detect(self, strings: List[Tuple[str, int]]) -> List[Dict[str, Any]]:
        findings = []
        for s, offset in strings:
            for match in self.regex.finditer(s):
                address = match.group()
                is_checksum_valid = self._validate_eip55(address)
                findings.append({
                    "type": "ETHEREUM_ADDRESS",
                    "address": address,
                    "offset": offset + match.start(),
                    "confidence": 0.95 if is_checksum_valid else 0.80,
                    "checksum_valid": is_checksum_valid
                })
        return findings
    
    def _validate_eip55(self, address: str) -> bool:
        """Checks if the address has EIP-55 style mixed case"""
        has_upper = any(c.isupper() for c in address)
        has_lower = any(c.islower() for c in address[2:])
        return has_upper and has_lower


class SolanaAddressDetector:
    """Detects Solana (Base58) addresses"""
    SOL_PATTERN = r'\b[1-9A-HJ-NP-Za-km-z]{32,44}\b'
    
    def __init__(self):
        self.regex = re.compile(self.SOL_PATTERN)
        
    def detect(self, strings: List[Tuple[str, int]]) -> List[Dict[str, Any]]:
        findings = []
        for s, offset in strings:
            for match in self.regex.finditer(s):
                address = match.group()
                entropy = ValidationUtils.calculate_entropy(address)
                # Solana addresses are usually very high entropy
                if entropy > 4.2:
                    findings.append({
                        "type": "SOLANA_ADDRESS",
                        "address": address,
                        "offset": offset + match.start(),
                        "confidence": 0.75,
                        "entropy": round(entropy, 2)
                    })
        return findings


class PrivateKeyDetector:
    """Detects high-entropy private keys and specific formats"""
    
    PATTERNS = {
        "WIF": r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b',
        "HEX_64": r'\b[0-9a-fA-F]{64}\b',
        "PEM": r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
    }
    
    def __init__(self):
        self.regexes = {k: re.compile(v) for k, v in self.PATTERNS.items()}
    
    def detect(self, strings: List[Tuple[str, int]]) -> List[Dict[str, Any]]:
        findings = []
        for s, offset in strings:
            # 1. Pattern Matching
            for p_type, regex in self.regexes.items():
                for match in regex.finditer(s):
                    val = match.group()
                    confidence = 0.40
                    severity = "medium"
                    
                    if p_type == "WIF":
                        if ValidationUtils.validate_btc_checksum(val):
                            confidence = 0.98
                            severity = "critical"
                    elif p_type == "HEX_64":
                        entropy = ValidationUtils.calculate_entropy(val)
                        if entropy > 3.8:
                            confidence = 0.65
                            # Context check
                            if any(k in s.lower() for k in ["key", "priv", "secret", "wallet", "seed"]):
                                confidence = 0.90
                                severity = "high"
                    
                    findings.append({
                        "type": f"PRIVATE_KEY_{p_type}",
                        "value_preview": val[:16] + "...",
                        "offset": offset + match.start(),
                        "confidence": confidence,
                        "severity": severity
                    })
            
            # 2. Raw Entropy Detection (possible binary/hex keys in strings)
            if 32 <= len(s) <= 128:
                entropy = ValidationUtils.calculate_entropy(s)
                if entropy > 4.8:
                    findings.append({
                        "type": "HIGH_ENTROPY_STRING",
                        "value_preview": s[:16] + "...",
                        "offset": offset,
                        "confidence": 0.35,
                        "entropy": round(entropy, 2),
                        "severity": "low"
                    })
        return findings


class TransactionHashDetector:
    """Detects blockchain transaction hashes"""
    
    TX_PATTERN = r'\b[a-fA-F0-9]{64}\b'
    
    def __init__(self):
        self.regex = re.compile(self.TX_PATTERN)
    
    def detect(self, strings: List[Tuple[str, int]]) -> List[Dict[str, Any]]:
        findings = []
        keywords = ["txid", "transaction", "tx_hash", "hash", "block"]
        
        for s, offset in strings:
            s_lower = s.lower()
            for match in self.regex.finditer(s):
                val = match.group()
                # Check for context within the string
                context_score = sum(1 for kw in keywords if kw in s_lower[max(0, match.start()-50):match.end()+50])
                
                if context_score > 0:
                    findings.append({
                        "type": "TRANSACTION_HASH",
                        "hash": val,
                        "offset": offset + match.start(),
                        "confidence": min(0.30 + (context_score * 0.20), 0.85),
                        "context_score": context_score
                    })
        return findings


class WalletTraceDetector:
    """Detects signatures of popular wallet software"""
    
    SIGNATURES = {
        "metamask": ["metamask", "nkbihfbeogaeaoehlefnkodbefgpgknn", "vault", "keyring"],
        "phantom": ["phantom", "bfnaoomekheghbehpbiidgfhehgmcjbf"],
        "ledger": ["ledger-live", "ledger device", "nanox", "nanos"],
        "trezor": ["trezor bridge", "trezord", "satoshilabs"],
        "trust": ["trustwallet", "trust-wallet"],
        "exodus": ["exodus.io", "exoduswallet"],
        "coinbase": ["coinbase-wallet", "hnfanknocfeofbdgbadclonhodhndhbb"]
    }
    
    def __init__(self):
        pass

    def detect(self, strings: List[Tuple[str, int]]) -> List[Dict[str, Any]]:
        findings = []
        for s, offset in strings:
            s_low = s.lower()
            for wallet, sigs in self.SIGNATURES.items():
                for sig in sigs:
                    if sig in s_low:
                        findings.append({
                            "type": "WALLET_TRACE",
                            "wallet": wallet,
                            "signature": sig,
                            "offset": offset,
                            "confidence": 0.80 if len(sig) > 20 else 0.50
                        })
                        break
        return findings


class AdvancedArtifactDetector:
    """Coordinates all cryptocurrency artifact detection modules"""
    
    def __init__(self):
        self.btc_detector = BitcoinAddressDetector()
        self.eth_detector = EthereumAddressDetector()
        self.sol_detector = SolanaAddressDetector()
        self.pk_detector = PrivateKeyDetector()
        self.wallet_detector = WalletTraceDetector()
        self.tx_detector = TransactionHashDetector()
    
    def detect_all(self, strings: List[Tuple[str, int]]) -> Dict[str, List[Dict[str, Any]]]:
        results = {
            "bitcoin_addresses": [],
            "ethereum_addresses": [],
            "solana_addresses": [],
            "private_key_indicators": [],
            "wallet_traces": [],
            "transaction_hashes": []
        }
        
        # Performance pass
        for s, offset in strings:
            results["bitcoin_addresses"].extend(self.btc_detector.detect([(s, offset)]))
            results["ethereum_addresses"].extend(self.eth_detector.detect([(s, offset)]))
            results["solana_addresses"].extend(self.sol_detector.detect([(s, offset)]))
            results["private_key_indicators"].extend(self.pk_detector.detect([(s, offset)]))
            results["wallet_traces"].extend(self.wallet_detector.detect([(s, offset)]))
            results["transaction_hashes"].extend(self.tx_detector.detect([(s, offset)]))
                
        return results

    def get_summary(self, results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        summary = {k: len(v) for k, v in results.items()}
        summary["total_artifacts"] = sum(summary.values())
        return summary


if __name__ == "__main__":
    # Test the detectors
    test_strings = [
        ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa is a legacy Bitcoin address", 0),
        ("0x742d35Cc6634C0532925a3b844Bc454e4438f44e is an Ethereum address", 200),
        ("5Kb8kLf9zgWQnogidDA76MzPL6TsZZY36hWXMssSzNydYXYB9KF is a WIF key", 400),
        ("metamask extension vault keyring", 500),
        ("HN7cABqLne4Ap6YV6oM5A9Y4r7j4bU4jU9bX", 600),
    ]
    
    detector = AdvancedArtifactDetector()
    results = detector.detect_all(test_strings)
    
    for category, findings in results.items():
        print(f"\n{category}: {len(findings)} findings")
        for finding in findings:
            print(f"  - {finding}")
