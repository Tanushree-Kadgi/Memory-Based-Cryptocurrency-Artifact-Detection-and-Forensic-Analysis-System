import os

def load_bip39_wordlist(path=None):
    """
    Load the BIP-39 English wordlist from disk.
    Searches for wordlists/bip39_english.txt relative to this file.
    """
    if path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "wordlists", "bip39_english.txt")

    with open(path, "r", encoding="utf-8") as f:
        words = set(line.strip().lower() for line in f if line.strip())

    print(f"[+] Loaded {len(words)} BIP-39 words from {path}")
    return words


def detect_seed_phrases(strings, bip39_words):

    findings = []

    context_keywords = ["seed", "wallet", "recovery", "phrase", "private"]

    for s, offset in strings:
        words = s.lower().split()

        for i in range(len(words) - 11):
            window = words[i:i+12]

            matches = sum(1 for w in window if w in bip39_words)

            if matches >= 10:  # relaxed threshold
                phrase = " ".join(window)

                # 🔥 CONTEXT CHECK
                context_score = 0
                for ck in context_keywords:
                    if ck in s.lower():
                        context_score += 1

                # 🔥 CONFIDENCE SCORE
                confidence = (matches / 12) * 100 + (context_score * 5)

                if confidence >= 70:  # threshold
                    findings.append({
                        "type": "SEED_PHRASE",
                        "phrase": phrase,
                        "offset": offset,
                        "word_count": len(window),
                        "matches": matches,
                        "confidence": round(confidence / 100, 2),
                        "context_score": context_score
                    })

    return findings