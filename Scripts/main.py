import argparse
import json
import os
from pathlib import Path
import sys

try:
    import fitz
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def extract_pdf_with_fitz(pdf_path: Path, output_dir: Path) -> dict:
    doc = fitz.open(pdf_path)
    text_by_page = {}
    tables = []
    images = []

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text("text")
        text_by_page[f"page_{page_number}"] = text.strip()

        for image_index, image_info in enumerate(page.get_images(full=True), start=1):
            xref = image_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image.get("ext", "png")
            image_name = (
                f"{pdf_path.stem}_page{page_number}_img{image_index}.{image_ext}"
            )
            image_path = output_dir / "images" / image_name
            ensure_dir(output_dir / "images")
            image_path.write_bytes(image_bytes)

            images.append(
                {
                    "page": page_number,
                    "image_index": image_index,
                    "xref": xref,
                    "width": base_image.get("width"),
                    "height": base_image.get("height"),
                    "colorspace": base_image.get("colorspace"),
                    "image_path": str(image_path.resolve()),
                }
            )

    return {
        "file_name": pdf_path.name,
        "file_path": str(pdf_path.resolve()),
        "text": text_by_page,
        "tables": tables,
        "images": images,
    }


def extract_tables_with_pdfplumber(pdf_path: Path) -> list:
    if pdfplumber is None:
        return []

    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_tables = page.extract_tables()
            for table_index, table in enumerate(page_tables, start=1):
                if not table or not any(
                    any(cell for cell in row if cell) for row in table
                ):
                    continue
                tables.append(
                    {
                        "page": page_number,
                        "table_index": table_index,
                        "rows": table,
                    }
                )
    return tables


def extract_all_reports(report_dir: Path, output_dir: Path) -> dict:
    output_dir = ensure_dir(output_dir)
    extracted = {"files": []}

    for pdf_path in sorted(report_dir.glob("*.pdf")):
        print(f"Processing {pdf_path.name}...")
        if fitz is None:
            raise RuntimeError(
                "PyMuPDF is required for this script. Install it with: pip install PyMuPDF"
            )

        file_output = extract_pdf_with_fitz(pdf_path, output_dir)
        file_output["tables"] = extract_tables_with_pdfplumber(pdf_path)
        if not file_output["tables"] and pdfplumber is None:
            print("Warning: pdfplumber is not installed, table extraction is disabled.")
        extracted["files"].append(file_output)

        text_file = output_dir / f"{pdf_path.stem}_text.json"
        text_file.write_text(
            json.dumps(file_output["text"], ensure_ascii=False, indent=2)
        )

        tables_file = output_dir / f"{pdf_path.stem}_tables.json"
        tables_file.write_text(
            json.dumps(file_output["tables"], ensure_ascii=False, indent=2)
        )

    return extracted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract text, images, and tables from PDF files in the Reports folder."
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "Reports",
        help="Directory containing PDF reports.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "Reports" / "extracted_output",
        help="Where extracted files and summary JSON will be written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_dir = args.reports_dir
    output_dir = args.output_dir

    if not report_dir.exists() or not report_dir.is_dir():
        print(f"Reports directory not found: {report_dir}")
        return 1

    if not any(report_dir.glob("*.pdf")):
        print(f"No PDF files found in reports directory: {report_dir}")
        return 1

    extracted = extract_all_reports(report_dir, output_dir)
    summary_path = output_dir / "extracted_summary.json"
    summary_path.write_text(json.dumps(extracted, ensure_ascii=False, indent=2))

    print(f"Extraction complete. Summary written to: {summary_path}")
    print(f"Images saved under: {output_dir / 'images'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
