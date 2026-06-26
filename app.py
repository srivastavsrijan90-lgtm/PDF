import io
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from utils import pdf_tools

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB
app.config["UPLOAD_FOLDER"] = Path(__file__).parent / "uploads"
app.config["UPLOAD_FOLDER"].mkdir(exist_ok=True)

ALLOWED_PDF = {"pdf"}
ALLOWED_IMAGE = {"png", "jpg", "jpeg", "webp", "gif", "bmp"}


def allowed_file(filename: str, extensions: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in extensions


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/page-count", methods=["POST"])
def page_count():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    if not allowed_file(f.filename, ALLOWED_PDF):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    try:
        count = pdf_tools.get_page_count(f.stream)
        f.stream.seek(0)
        return jsonify({"pages": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/merge", methods=["POST"])
def merge():
    files = request.files.getlist("files")
    if len(files) < 2:
        return jsonify({"error": "Upload at least 2 PDF files"}), 400
    streams = []
    for f in files:
        if not allowed_file(f.filename, ALLOWED_PDF):
            return jsonify({"error": f"Invalid file: {f.filename}"}), 400
        streams.append(f.stream)
    try:
        result = pdf_tools.merge_pdfs(streams)
        return send_file(
            io.BytesIO(result),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="merged.pdf",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/split", methods=["POST"])
def split():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    ranges = request.form.get("ranges", "1")
    f = request.files["file"]
    if not allowed_file(f.filename, ALLOWED_PDF):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    try:
        parts = pdf_tools.split_pdf(f.stream, ranges)
        if len(parts) == 1:
            return send_file(
                io.BytesIO(parts[0][1]),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=parts[0][0],
            )
        zipped = pdf_tools.zip_files(parts)
        return send_file(
            io.BytesIO(zipped),
            mimetype="application/zip",
            as_attachment=True,
            download_name="split_pdfs.zip",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rotate", methods=["POST"])
def rotate():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    rotation = int(request.form.get("rotation", 90))
    pages = request.form.get("pages", "")
    f = request.files["file"]
    if not allowed_file(f.filename, ALLOWED_PDF):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    try:
        result = pdf_tools.rotate_pdf(f.stream, rotation, pages or None)
        return send_file(
            io.BytesIO(result),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="rotated.pdf",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/compress", methods=["POST"])
def compress():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    if not allowed_file(f.filename, ALLOWED_PDF):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    try:
        original_size = len(f.read())
        f.stream.seek(0)
        result = pdf_tools.compress_pdf(f.stream)
        compressed_size = len(result)
        return send_file(
            io.BytesIO(result),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="compressed.pdf",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/extract-text", methods=["POST"])
def extract_text():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    if not allowed_file(f.filename, ALLOWED_PDF):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    try:
        text = pdf_tools.extract_text(f.stream)
        return send_file(
            io.BytesIO(text.encode("utf-8")),
            mimetype="text/plain",
            as_attachment=True,
            download_name="extracted_text.txt",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/watermark", methods=["POST"])
def watermark():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    text = request.form.get("watermark", "CONFIDENTIAL")
    f = request.files["file"]
    if not allowed_file(f.filename, ALLOWED_PDF):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    try:
        result = pdf_tools.add_watermark(f.stream, text)
        return send_file(
            io.BytesIO(result),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="watermarked.pdf",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reorder", methods=["POST"])
def reorder():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    order = request.form.get("order", "")
    if not order:
        return jsonify({"error": "Page order is required"}), 400
    f = request.files["file"]
    if not allowed_file(f.filename, ALLOWED_PDF):
        return jsonify({"error": "Only PDF files are allowed"}), 400
    try:
        result = pdf_tools.reorder_pages(f.stream, order)
        return send_file(
            io.BytesIO(result),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="reordered.pdf",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/images-to-pdf", methods=["POST"])
def images_to_pdf():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "Upload at least 1 image"}), 400
    streams = []
    for f in files:
        if not allowed_file(f.filename, ALLOWED_IMAGE):
            return jsonify({"error": f"Invalid image: {f.filename}"}), 400
        streams.append(f.stream)
    try:
        result = pdf_tools.images_to_pdf(streams)
        return send_file(
            io.BytesIO(result),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="images.pdf",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 50 MB."}), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
