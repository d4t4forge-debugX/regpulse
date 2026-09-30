import fitz  # PyMuPDF

def render_page_as_image(pdf_path, page_number, output_path, zoom=2.0):
    doc = fitz.open(pdf_path)
    page = doc[page_number]
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix)
    pix.save(output_path)
    doc.close()

if __name__ == "__main__":
    render_page_as_image("apple_10k.pdf", page_number=0, output_path="apple_10k_page1.png")
    print("Saved apple_10k_page1.png")