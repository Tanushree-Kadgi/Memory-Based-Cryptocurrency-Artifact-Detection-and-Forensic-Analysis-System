from modules.extractor import extract_strings, search_keyword
from modules.detector import load_bip39_wordlist, detect_seed_phrases
from modules.analyzer import analyze
from modules.reporter import generate_report
import os

print("===== SEEDTRACE TOOL =====")

# ---------------- USER INPUT ---------------- #

dump_file = input("Enter path of memory dump file (e.g., tools/test.raw): ").strip()

if not os.path.exists(dump_file):
    print("[!] File not found. Exiting.")
    exit()

user_keyword = input("Enter keyword (optional, press Enter to skip): ").strip()

# ---------------- INTELLIGENT KEYWORDS ---------------- #

default_keywords = ["seed", "wallet", "recovery", "private", "mnemonic"]

# Combine user + default
keywords = default_keywords.copy()

if user_keyword:
    keywords.append(user_keyword)

print("\n[*] Keywords used for scanning:", keywords)

print("\n[*] Starting Analysis...\n")

# ---------------- STEP 1: KEYWORD SCAN ---------------- #

print("[*] Performing keyword scan...")
keyword_hits = False

for k in keywords:
    result = search_keyword(dump_file, k)
    if result:
        keyword_hits = True

# ---------------- STEP 2: EXTRACT STRINGS ---------------- #

print("\n[*] Extracting strings (this may take time)...")
strings = extract_strings(dump_file)

# ---------------- STEP 3: LOAD WORDLIST ---------------- #

words = load_bip39_wordlist()

# ---------------- STEP 4: DETECT SEED PHRASES ---------------- #

print("\n[*] Detecting seed phrases...")
findings = detect_seed_phrases(strings, words)

# ---------------- STEP 5: ANALYZE ---------------- #

analysis = analyze(findings, keyword_found=keyword_hits)

# ---------------- STEP 6: GENERATE REPORT ---------------- #

generate_report(analysis, dump_file)

# ---------------- FINAL OUTPUT ---------------- #

print("\n===== FINAL RESULT =====")
print(f"Risk Level: {analysis['risk']}")
print(f"Message: {analysis['message']}")

if findings:
    print("\n[+] Seed Candidates Found:\n")
    for f in findings:
        print(f"Phrase: {f['phrase']}")
        print(f"Confidence: {f.get('confidence','N/A')}%")
        print(f"Offset: {f['offset']}")
        print("-" * 40)
else:
    print("\n[-] No seed phrases detected.")

print("\n[*] Process Completed!")