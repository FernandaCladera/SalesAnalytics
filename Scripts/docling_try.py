from docling.document_converter import DocumentConverter

source = "../Reports/240312_Tecan_Presentation_FYR-2023.pdf"
converter = DocumentConverter()
doc = converter.convert(source).document
print(doc.export_to_markdown())
