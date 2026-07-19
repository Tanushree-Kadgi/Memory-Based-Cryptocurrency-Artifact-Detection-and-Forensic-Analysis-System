"""
Advanced PDF Report Generator for SeedTrace
Generates professional forensic reports with structured sections and case metadata
"""
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class PDFReportGenerator:
    """Generate professional forensic PDF reports"""
    
    COLORS = {
        "critical": "#dc2626",
        "high": "#f97316",
        "medium": "#eab308",
        "low": "#22c55e",
        "none": "#6b7280",
        "primary": "#1e293b",
        "secondary": "#334155",
        "accent": "#3b82f6",
        "background": "#f8fafc",
        "border": "#e2e8f0"
    }
    
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        self.custom_styles = {
            'Title': ParagraphStyle('ForensicTitle', parent=self.styles['Heading1'], fontSize=26, textColor=colors.HexColor(self.COLORS["primary"]), alignment=TA_CENTER, spaceAfter=20),
            'Heading2': ParagraphStyle('ForensicHeading2', parent=self.styles['Heading2'], fontSize=16, textColor=colors.HexColor(self.COLORS["secondary"]), spaceBefore=20, borderPadding=5, borderLeftColor=colors.HexColor(self.COLORS["accent"]), borderLeftWidth=3),
            'Heading3': ParagraphStyle('ForensicHeading3', parent=self.styles['Heading3'], fontSize=12, textColor=colors.HexColor(self.COLORS["secondary"]), spaceBefore=12),
            'Normal': ParagraphStyle('ForensicNormal', parent=self.styles['Normal'], fontSize=10, textColor=colors.HexColor(self.COLORS["primary"]), spaceAfter=8, leading=14),
            'TableHead': ParagraphStyle('TableHead', parent=self.styles['Normal'], fontSize=9, textColor=colors.white, fontName='Helvetica-Bold'),
            'TableText': ParagraphStyle('TableText', parent=self.styles['Normal'], fontSize=8),
            'Badge': ParagraphStyle('Badge', parent=self.styles['Normal'], fontSize=9, textColor=colors.white, alignment=TA_CENTER, borderPadding=3)
        }

    def _get_file_hashes(self, filepath: str) -> Dict[str, str]:
        """Generate MD5 and SHA256 hashes for evidence verification"""
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5.update(chunk)
                    sha256.update(chunk)
            return {"md5": md5.hexdigest(), "sha256": sha256.hexdigest()}
        except Exception:
            return {"md5": "N/A", "sha256": "N/A"}

    def generate_report(self, dump_file: str, analysis_result: Dict[str, Any], case_info: Dict[str, str] = None) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"SeedTrace_Forensic_Report_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        story = []
        
        # Default case info if not provided
        if not case_info:
            case_info = {
                "Case ID": f"CASE-{datetime.now().year}-{timestamp[:8]}",
                "Examiner": "SeedTrace Automated System",
                "Department": "Digital Forensics Unit",
                "Subject": os.path.basename(dump_file)
            }
            
        hashes = self._get_file_hashes(dump_file)
        
        # 1. TITLE PAGE
        story.append(Spacer(1, 1 * inch))
        story.append(Paragraph("FORENSIC ANALYSIS REPORT", self.custom_styles['Title']))
        story.append(Paragraph("SeedTrace Memory Artifact Recovery System", ParagraphStyle('Sub', alignment=TA_CENTER, fontSize=14, spaceAfter=40)))
        story.append(Spacer(1, 0.5 * inch))
        
        # Case Summary Table
        case_data = [
            ["CASE INFORMATION", ""],
            ["Case Identifier:", case_info.get("Case ID", "N/A")],
            ["Lead Examiner:", case_info.get("Examiner", "N/A")],
            ["Examination Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Evidence Source:", os.path.basename(dump_file)],
            ["Verification (MD5):", hashes['md5'][:32]],
            ["Verification (SHA256):", hashes['sha256'][:32] + "..."]
        ]
        
        t = Table(case_data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor(self.COLORS["secondary"])),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(self.COLORS["border"])),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(PageBreak())
        
        # 2. EXECUTIVE SUMMARY
        story.append(Paragraph("1. Executive Summary", self.custom_styles['Heading2']))
        risk = analysis_result.get("risk", "none").upper()
        risk_color = self.COLORS.get(analysis_result.get("risk", "none"), self.COLORS["none"])
        
        summary_text = (
            f"An automated forensic examination was conducted on the memory dump <b>{os.path.basename(dump_file)}</b>. "
            f"The primary objective was the identification and recovery of cryptocurrency-related artifacts, including seed phrases, private keys, and wallet identifiers. "
            f"<br/><br/>Findings indicate a <b><font color='{risk_color}'>{risk}</font></b> risk level. "
            f"A total of <b>{analysis_result.get('artifact_summary', {}).get('total_artifacts', 0)}</b> significant artifacts were identified during the analysis pass."
        )
        story.append(Paragraph(summary_text, self.custom_styles['Normal']))
        
        # Tool Value Section
        story.append(Paragraph("Aims & Capabilities:", self.custom_styles['Heading3']))
        story.append(Paragraph(
            "SeedTrace is designed to identify exposure of sensitive cryptographic data in volatile memory (RAM). "
            "It assists investigators in recovering recovery phrases, validating blockchain addresses through checksum analysis, "
            "and identifying established wallet software signatures that may have been present on the target system.",
            self.custom_styles['Normal']
        ))

        # Artifact Summary Table
        summary = analysis_result.get('artifact_summary', {})
        stats_data = [
            ["Artifact Category", "Count", "Forensic Significance"],
            ["Seed Phrases", str(summary.get('seed_phrases', 0)), "CRITICAL / FULL RECOVERY"],
            ["Private Keys", str(summary.get('private_keys', 0)), "CRITICAL / ASSET ACCESS"],
            ["Solana Addr", str(summary.get('solana_addresses', 0)), "HIGH / TARGET ID"],
            ["Bitcoin Addr", str(summary.get('bitcoin_addresses', 0)), "HIGH / TARGET ID"],
            ["Ethereum Addr", str(summary.get('ethereum_addresses', 0)), "HIGH / TARGET ID"],
            ["Wallet Traces", str(summary.get('wallet_traces', 0)), "MEDIUM / SOFTWARE ID"]
        ]
        
        st = Table(stats_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["accent"])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(self.COLORS["border"])),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ]))
        story.append(st)
        
        # 3. METHODOLOGY
        story.append(Paragraph("2. Methodology & Scope", self.custom_styles['Heading2']))
        method_text = (
            "The analysis utilized advanced string extraction, regex-based pattern matching, and cryptographic validation techniques. "
            "Validation was performed using Base58Check checksum verification for Bitcoin and EIP-55 case-analysis for Ethereum. "
            "Additionally, Shannon Entropy calculations were applied to identify potential non-standard private keys and high-entropy secrets. "
            "Wallet trace detection identifies known application signatures and browser extension identifiers."
        )
        story.append(Paragraph(method_text, self.custom_styles['Normal']))
        
        # 4. DETAILED FINDINGS
        story.append(Paragraph("3. Detailed Findings", self.custom_styles['Heading2']))
        
        artifacts = analysis_result.get("additional_artifacts", {})
        
        # Seed Phrases
        if analysis_result.get("findings"):
            story.append(Paragraph("3.1 Seed Phrases (Recovery Mnemonics)", self.custom_styles['Heading3']))
            story.append(Paragraph(
                "<b>Implication:</b> Seed phrases allow for the complete reconstruction of a wallet's private keys. "
                "Finding these in memory suggests that a wallet was recently created, imported, or accessed.",
                self.custom_styles['Normal']
            ))
            self._add_seed_table(story, analysis_result["findings"])
            
        # Private Keys
        if artifacts.get("private_key_indicators"):
            story.append(Paragraph("3.2 Potential Private Keys & High-Entropy Secrets", self.custom_styles['Heading3']))
            story.append(Paragraph(
                "<b>Implication:</b> Private keys provide direct access to specific blockchain accounts. "
                "Detection of high-entropy strings indicates the presence of cryptographic material that requires further inspection.",
                self.custom_styles['Normal']
            ))
            self._add_pk_table(story, artifacts["private_key_indicators"])
            
        # Addresses
        if artifacts.get("bitcoin_addresses") or artifacts.get("ethereum_addresses") or artifacts.get("solana_addresses"):
            story.append(Paragraph("3.3 Recovered Blockchain Addresses", self.custom_styles['Heading3']))
            story.append(Paragraph(
                "<b>Implication:</b> Addresses act as public identifiers. Identifying these helps in mapping the subject's transaction history "
                "across decentralized ledgers.",
                self.custom_styles['Normal']
            ))
            all_addrs = []
            if artifacts.get("bitcoin_addresses"): all_addrs.extend(artifacts["bitcoin_addresses"])
            if artifacts.get("ethereum_addresses"): all_addrs.extend(artifacts["ethereum_addresses"])
            if artifacts.get("solana_addresses"): all_addrs.extend(artifacts["solana_addresses"])
            self._add_address_table(story, all_addrs)
            
        # Wallet Traces
        if artifacts.get("wallet_traces"):
            story.append(Paragraph("3.4 Wallet Application Traces", self.custom_styles['Heading3']))
            story.append(Paragraph(
                "<b>Implication:</b> These traces confirm the specific wallet software used (e.g., MetaMask, Ledger). "
                "This helps narrow down where sensitive files or secondary artifacts might be located on the filesystem.",
                self.custom_styles['Normal']
            ))
            self._add_wallet_table(story, artifacts["wallet_traces"])
            
        # 5. CONCLUSION
        story.append(PageBreak())
        story.append(Paragraph("4. Conclusion & Recommendations", self.custom_styles['Heading2']))
        
        conclusion_map = {
            "critical": "Critical sensitive data (Seed Phrases) was found. The subject's cryptocurrency assets should be considered compromised.",
            "high": "High-confidence indicators and multiple addresses were found. Active cryptocurrency usage is highly likely.",
            "medium": "Several traces and addresses were found. Further investigation into the specific wallet software is recommended.",
            "low": "Minimal traces were found. No high-risk artifacts identified.",
            "none": "No cryptocurrency-related artifacts were detected in the provided evidence."
        }
        story.append(Paragraph(conclusion_map.get(analysis_result.get("risk", "none"), ""), self.custom_styles['Normal']))
        
        rec_text = (
            "<b>Recommendations:</b><br/>"
            "1. Correlation analysis with filesystem artifacts (e.g., AppData, browser profiles).<br/>"
            "2. Network forensics to identify blockchain node connections or API calls.<br/>"
            "3. If seed phrases were found, rotate funds immediately (under proper legal guidance)."
        )
        story.append(Paragraph(rec_text, self.custom_styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return filepath

    def _add_seed_table(self, story, findings):
        data = [["Offset", "Phrase Preview", "Confidence"]]
        for f in findings[:10]:
            data.append([
                hex(f.get('offset', 0)),
                f.get('phrase', 'N/A')[:40] + "...",
                f"{f.get('confidence', 0)*100:.0f}%"
            ])
        t = Table(data, colWidths=[1.2*inch, 4*inch, 1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["critical"])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(self.COLORS["border"])),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2*inch))

    def _add_pk_table(self, story, indicators):
        data = [["Type", "Preview", "Severity", "Confidence"]]
        for i in indicators[:15]:
            data.append([
                i.get('type', 'N/A'),
                i.get('value_preview', 'N/A'),
                i.get('severity', 'medium').upper(),
                f"{i.get('confidence', 0)*100:.0f}%"
            ])
        t = Table(data, colWidths=[1.8*inch, 2.4*inch, 1*inch, 1*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["high"])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(self.COLORS["border"])),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2*inch))

    def _add_address_table(self, story, addresses):
        data = [["Blockchain Type", "Address", "Valid?", "Offset"]]
        for a in addresses[:20]:
            data.append([
                a.get('type', 'N/A'),
                a.get('address', 'N/A')[:35] + ("..." if len(a.get('address', '')) > 35 else ""),
                "YES" if a.get('checksum_valid') else "N/A",
                hex(a.get('offset', 0))
            ])
        t = Table(data, colWidths=[1.6*inch, 3*inch, 0.8*inch, 0.8*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["accent"])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(self.COLORS["border"])),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2*inch))

    def _add_wallet_table(self, story, wallets):
        data = [["Wallet Software", "Signature Match", "Confidence"]]
        for w in wallets[:15]:
            data.append([
                w.get('wallet', 'N/A').upper(),
                w.get('signature', 'N/A'),
                f"{w.get('confidence', 0)*100:.0f}%"
            ])
        t = Table(data, colWidths=[1.5*inch, 3.2*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.COLORS["medium"])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(self.COLORS["border"])),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2*inch))


if __name__ == "__main__":
    generator = PDFReportGenerator()
    test_res = {
        "risk": "critical",
        "artifact_summary": {"total_artifacts": 10, "seed_phrases": 1, "private_keys": 2},
        "findings": [{"offset": 1000, "phrase": "word1 word2 ... word12", "confidence": 0.95}],
        "additional_artifacts": {
            "private_key_indicators": [{"type": "PRIVATE_KEY_WIF", "value_preview": "5KL...", "severity": "critical", "confidence": 0.98}],
            "bitcoin_addresses": [{"type": "BITCOIN_ADDRESS_LEGACY", "address": "1A1zP1...", "checksum_valid": True, "offset": 2000}]
        }
    }
    generator.generate_report("sample_dump.raw", test_res)
