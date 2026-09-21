import pypdf

reader = pypdf.PdfReader('sih26155_agent/compliance_audit_report_2026-09-19.pdf')
print('Generated PDF Total Pages:', len(reader.pages))

sections_to_check = [
    'GAACA',
    'GENERAL AUTONOMOUS AGENT COGNITIVE ARCHITECTURE',
    'NETWORK SECURITY & CONFIGURATION',
    'COMPLIANCE AUDIT REPORT',
    'Report ID',
    'Purpose',
    'Authority & Baseline',
    '1. Executive Summary',
    'Management Conclusion',
    '2. Audit Scope & Context',
    '3. Asset Inventory',
    '4. Assessment Methodology',
    '5. Findings Register',
    '6. Detailed Finding',
    '7. Control Assessment Matrix',
    '8. Human Review & Unknown Syntax',
    '9. Evidence Register',
    '10. Risk Register',
    '11. Remediation Plan',
    '12. Compliance Authority Register',
    '13. Governance, Review & Approval',
    '14. Audit Trail Summary',
    '15. Appendix',
    '16. Report Integrity Rules',
]

full_text = ''
for i, page in enumerate(reader.pages):
    txt = page.extract_text() or ''
    full_text += f'\n--- Page {i+1} ---\n' + txt
    print(f'Page {i+1} character count: {len(txt)}')

with open('scratch/new_compliance_extracted.txt', 'w', encoding='utf-8') as f:
    f.write(full_text)

print('\nSection Verification:')
all_passed = True
for sec in sections_to_check:
    found = sec.lower() in full_text.lower()
    res = 'PASS' if found else 'FAIL'
    if not found:
        all_passed = False
    print(f'  [{res}] {sec}')

print('\nAll sections verified:', all_passed)
