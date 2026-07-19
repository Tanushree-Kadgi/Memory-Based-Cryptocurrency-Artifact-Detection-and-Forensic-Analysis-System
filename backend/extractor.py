import re
import os
import time

def extract_strings(dump_path, min_length=10, chunk_size=100*1024*1024, progress_callback=None):
    """
    Extract readable ASCII strings from RAM dump
    Optimized for faster processing with larger chunk size
    """

    # Pattern: printable ASCII characters
    pattern = re.compile(rb'[ -~]{' + str(min_length).encode() + rb',}')

    strings_found = []
    offset = 0
    total_size = os.path.getsize(dump_path)

    print(f"[*] Extracting strings from {dump_path} (chunk size: {chunk_size/(1024**2):.0f} MB)")

    with open(dump_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            for match in pattern.finditer(chunk):
                string = match.group().decode('ascii', errors='ignore')
                absolute_offset = offset + match.start()
                strings_found.append((string, absolute_offset))

            offset += len(chunk)
            percent = (offset / total_size) * 100 if total_size > 0 else 0
            
            # Print to console for terminal visibility
            if int(percent) % 2 == 0:
                print(f"[*] Extraction Progress: {percent:.1f}% ({offset / (1024**3):.2f} GB processed)")

            # IMPORTANT: Yield the GIL to allow the Flask API to respond to polling requests
            time.sleep(0.01)

            if progress_callback:
                progress_callback(percent, offset)


    print(f"[+] Extraction complete. Found {len(strings_found)} strings.")
    return strings_found

def search_keyword(dump_path, keyword="abandon", chunk_size=100*1024*1024, progress_callback=None):
    keyword = keyword.lower().encode()
    found = []
    total_size = os.path.getsize(dump_path)

    print(f"[*] Searching for keyword: {keyword.decode()}")

    with open(dump_path, 'rb') as f:
        offset = 0

        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            if keyword in chunk.lower():
                print(f"[+] Found at offset: {offset}")
                found.append(offset)

            offset += len(chunk)
            
            # Yield GIL
            time.sleep(0.01)

            if progress_callback:
                percent = (offset / total_size) * 100
                progress_callback(percent, offset)

    print(f"[+] Total occurrences: {len(found)}")
    return found



def view_at_offset(dump_path, offset, window=200):
    """
    View readable data around a specific memory offset
    """
    with open(dump_path, 'rb') as f:
        f.seek(offset)

        data = f.read(window)

        try:
            text = data.decode('ascii', errors='ignore')
        except:
            text = str(data)

        print(f"\n[Offset {offset}]")
        print("-" * 50)
        print(text)
        print("-" * 50)


def search_and_show(dump_path, keyword="abandon", context=200):
    keyword_bytes = keyword.encode()

    with open(dump_path, 'rb') as f:
        offset = 0

        while True:
            chunk = f.read(50*1024*1024)
            if not chunk:
                break

            pos = chunk.lower().find(keyword_bytes)
            if pos != -1:
                f.seek(offset + pos - context)
                data = f.read(context * 2)

                print("\n[FOUND CONTEXT]")
                print("-" * 50)
                print(data.decode('ascii', errors='ignore'))
                print("-" * 50)
                return

            offset += len(chunk)