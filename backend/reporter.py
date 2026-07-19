import os
from datetime import datetime

def generate_report(analysis, dump_file):
    try:
        os.makedirs("reports", exist_ok=True)

        filename = os.path.join(
            "reports",
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        with open(filename, "w", encoding="utf-8") as f:
            # HEADER
            f.write("===== SEEDTRACE REPORT =====\n\n")
            f.write(f"Dump File: {dump_file}\n\n")

            # RISK INFO
            f.write(f"RISK LEVEL: {analysis.get('risk','UNKNOWN')}\n")
            f.write(f"DETAILS: {analysis.get('message','N/A')}\n\n")

            # 🔥 NEW DETAILED FINDINGS
            if analysis.get('findings'):
                f.write("Detected Seed Candidates:\n\n")

                for item in analysis['findings']:
                    f.write(f"Phrase: {item.get('phrase','N/A')}\n")
                    f.write(f"Offset: {item.get('offset','N/A')}\n")
                    f.write(f"Matches: {item.get('matches','N/A')}/12\n")
                    f.write(f"Confidence: {item.get('confidence','N/A')}%\n")
                    f.write(f"Context Score: {item.get('context_score','N/A')}\n")
                    f.write("-" * 40 + "\n")

            else:
                f.write("No seed phrases detected.\n")

            # 🔥 NOTE SECTION (VERY IMPORTANT)
            f.write("\nNOTE:\n")
            f.write("Memory artifacts are volatile and may disappear quickly.\n")
            f.write("Detection depends on user interaction and timing of memory acquisition.\n")

        print(f"[+] Report saved successfully at: {filename}")

    except Exception as e:
        print(f"[!] Report generation failed: {e}")