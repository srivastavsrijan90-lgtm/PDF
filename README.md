# PDF Studio

A beautiful, all-in-one PDF toolkit built with **Flask** and **pypdf**.

## Features

| Tool | Description |
|------|-------------|
| **Merge** | Combine multiple PDFs into one |
| **Split** | Extract pages by range (e.g. `1-3, 5, 7-9`) |
| **Rotate** | Rotate pages 90°, 180°, or 270° |
| **Compress** | Optimize and reduce PDF file size |
| **Extract Text** | Pull text content into a `.txt` file |
| **Watermark** | Add a diagonal text watermark |
| **Reorder** | Rearrange pages in custom order |
| **Images → PDF** | Convert images to a single PDF |

## Quick Start

```bash
cd pdf_app
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

## Requirements

- Python 3.10+
- See `requirements.txt` for packages

## Notes

- Maximum upload size: **50 MB**
- Files are processed in memory and not stored permanently
- Drag & drop or click to upload files
