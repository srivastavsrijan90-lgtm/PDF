import io
import zipfile

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def merge_pdfs(file_streams: list) -> bytes:
    writer = PdfWriter()
    for stream in file_streams:
        reader = PdfReader(stream)
        for page in reader.pages:
            writer.add_page(page)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def split_pdf(file_stream, page_ranges: str) -> list[tuple[str, bytes]]:
    """Split PDF by page ranges. Format: '1-3,5,7-9' (1-indexed)."""
    reader = PdfReader(file_stream)
    total = len(reader.pages)
    results = []

    for part in page_ranges.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            start_idx = max(0, int(start) - 1)
            end_idx = min(total, int(end))
        else:
            start_idx = int(part) - 1
            end_idx = start_idx + 1

        writer = PdfWriter()
        for i in range(start_idx, end_idx):
            if 0 <= i < total:
                writer.add_page(reader.pages[i])

        output = io.BytesIO()
        writer.write(output)
        label = part.replace("-", "_")
        results.append((f"pages_{label}.pdf", output.getvalue()))

    return results


def rotate_pdf(file_stream, rotation: int, pages: str | None = None) -> bytes:
    reader = PdfReader(file_stream)
    writer = PdfWriter()
    total = len(reader.pages)

    target_pages = set(range(total))
    if pages:
        target_pages = set()
        for part in pages.replace(" ", "").split(","):
            if "-" in part:
                start, end = part.split("-", 1)
                target_pages.update(range(int(start) - 1, int(end)))
            else:
                target_pages.add(int(part) - 1)

    for i, page in enumerate(reader.pages):
        if i in target_pages:
            page.rotate(rotation)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def compress_pdf(file_stream) -> bytes:
    writer = PdfWriter()
    reader = PdfReader(file_stream)
    for page in reader.pages:
        writer.add_page(page)
    for page in writer.pages:
        page.compress_content_streams()
    writer.compress_identical_objects(remove_identicals=True)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def extract_text(file_stream) -> str:
    reader = PdfReader(file_stream)
    texts = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        texts.append(f"--- Page {i} ---\n{text}")
    return "\n\n".join(texts)



def images_to_pdf(file_streams: list) -> bytes:
    images = []
    for stream in file_streams:
        img = Image.open(stream)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        images.append(img)

    output = io.BytesIO()
    if len(images) == 1:
        images[0].save(output, format="PDF")
    else:
        images[0].save(output, format="PDF", save_all=True, append_images=images[1:])
    return output.getvalue()


def add_watermark(file_stream, watermark_text: str) -> bytes:
    reader = PdfReader(file_stream)
    writer = PdfWriter()

    watermark_buf = io.BytesIO()
    c = canvas.Canvas(watermark_buf, pagesize=letter)
    c.setFont("Helvetica", 40)
    c.setFillAlpha(0.3)
    c.saveState()
    c.translate(300, 400)
    c.rotate(45)
    c.drawCentredString(0, 0, watermark_text)
    c.restoreState()
    c.save()
    watermark_buf.seek(0)
    watermark_page = PdfReader(watermark_buf).pages[0]

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def get_page_count(file_stream) -> int:
    reader = PdfReader(file_stream)
    return len(reader.pages)


def reorder_pages(file_stream, order: str) -> bytes:
    """Reorder pages. Format: '3,1,2' (1-indexed)."""
    reader = PdfReader(file_stream)
    writer = PdfWriter()
    indices = [int(x.strip()) - 1 for x in order.split(",") if x.strip()]
    for idx in indices:
        if 0 <= idx < len(reader.pages):
            writer.add_page(reader.pages[idx])
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def zip_files(named_files: list[tuple[str, bytes]]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in named_files:
            zf.writestr(name, data)
    return buf.getvalue()
