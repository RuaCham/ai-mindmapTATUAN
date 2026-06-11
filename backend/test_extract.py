"""
Chạy: python test_extract.py <đường_dẫn_file.pdf>
In ra text extract được + headings detect được
"""
import sys, json
sys.path.insert(0, ".")

def test(pdf_path: str):
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    from app.services.pdf_service import extract_text
    from app.services.layout_service import detect_headings
    from app.services.keyword_service import extract_keywords

    result   = extract_text(pdf_bytes)
    text     = result["text"]
    blocks   = result["blocks"]
    quality  = result["quality"]

    print(f"\n{'='*60}")
    print(f"QUALITY  : {quality}")
    print(f"PAGES    : {result['num_pages']}")
    print(f"CHARS    : {len(text)}")
    print(f"\n--- TEXT (500 ký tự đầu) ---")
    print(text[:500])
    print(f"\n--- HEADINGS ---")
    headings = detect_headings(text, blocks)
    for h in headings[:20]:
        indent = "  " * (h["level"] - 1)
        print(f"{indent}[L{h['level']}] {h['text']}")
    print(f"\nTổng: {len(headings)} headings")
    print(f"\n--- TOP KEYWORDS ---")
    kws = extract_keywords(text, top_n=15)
    for k, v in kws.items():
        print(f"  {k}: {v:.4f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_extract.py <path_to_pdf>")
    else:
        test(sys.argv[1])
