import os
import random

def generate_fake_dump(output_path="test_dump.raw", size_mb=10):
    """
    Generates a mock RAM dump file containing realistic forensic artifacts for testing.
    """
    print(f"[*] Generating mock RAM dump ({size_mb} MB)...")
    
    # 1. Initialize with random noise
    data = bytearray(os.urandom(size_mb * 1024 * 1024))
    
    # 2. Define a comprehensive set of artifacts
    artifacts = [
        # --- SEED PHRASES ---
        # 12-word BIP-39 mnemonic
        (1024 * 50, b"abandon ability able about above absent absorb abstract absurd abuse access accident"),
        # 24-word BIP-39 mnemonic
        (1024 * 100, b"all animal army armor arctic architecture area argue arise arm armed armor army around arrange arrest arrive arrow art article artificial artist as ash"),

        # --- BLOCKCHAIN ADDRESSES ---
        # Bitcoin Legacy (Valid Checksum)
        (1024 * 200, b"1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"), 
        # Bitcoin P2SH (Valid Checksum)
        (1024 * 250, b"3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"),
        # Bitcoin BECH32 (SegWit)
        (1024 * 300, b"bc1qcr8te0ex6f4hwz09eoq6p7e39r9m9slas9z6ms"),
        
        # Ethereum Address (EIP-55 Mixed Case - Valid)
        (1024 * 350, b"0x742D35cc6634C0532925a3B844Bc454E4438f44E"),
        # Ethereum Address (Lower Case - Detectable but lower confidence)
        (1024 * 400, b"0x0d8775f648430679a709e98d2b0ef625062489e1"),
        
        # Solana Address (Base58)
        (1024 * 450, b"v6Y5V89D6D8v9X6H9X6H9X6H9X6H9X6H9X6H9X6H9X6"), # Entropy filtered SOL address

        # --- PRIVATE KEYS ---
        # Bitcoin WIF (Compressed - Valid Checksum)
        (1024 * 500, b"L1v6X5y8b2X5V89D6D8v9X6H9X6H9X6H9X6H9X6H9X6H9X6H9X6H"), # Fake but formatted
        (1024 * 520, b"5Kb8kLf9zgWQnogidDA76MzPL6TsZZY36hWXMssSzNydYXYB9KF"), # Real WIF example
        
        # Raw 64-char Hex (Secret) with context
        (1024 * 600, b"user_private_key = \"4c1a5d2e3b6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b\""),
        
        # PEM EC Private Key
        (1024 * 700, b"-----BEGIN EC PRIVATE KEY-----\nMHQCAQEEIBJ...base64data...\n-----END EC PRIVATE KEY-----"),

        # --- WALLET TRACES ---
        # MetaMask signature
        (1024 * 850, b"metamask_vault_keyring = {\"data\": \"...\"}"),
        # Chrome Extension Path
        (1024 * 900, b"chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/index.html"),
        # Ledger Protocol
        (1024 * 950, b"ledger-live://bridge?target=usb"),
        # Phantom Extension
        (1024 * 1000, b"chrome-extension://bfnaoomekheghbehpbiidgfhehgmcjbf/popup.html"),

        # --- BLOCKCHAIN METADATA ---
        # Transaction IDs
        (1024 * 1100, b"last_txid: a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d"),
        (1024 * 1150, b"hash: 00000000000000000000123456789abcdef0123456789abcdef0123456789abc"),

        # --- MISC SENSITIVE ---
        # High Entropy String (Potential credential)
        (1024 * 1300, b"amFkZ2UuY29tL3Byb2plY3RzL3NlZWR0cmFjZS1hZHZhbmNlZC1mb3JlbnNpY3M="),
    ]
    
    # 3. Inject artifacts at specified offsets
    for offset, content in artifacts:
        data[offset:offset+len(content)] = content
        print(f" [+] Injected {content[:20]}... at offset {hex(offset)}")
        
    # 4. Save to file
    with open(output_path, "wb") as f:
        f.write(data)
        
    print(f"\n[!] Success: Mock dump created at {os.path.abspath(output_path)}")
    print(f"[!] You can now upload this file to SeedTrace for testing.")

if __name__ == "__main__":
    generate_fake_dump()
