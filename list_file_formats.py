import os
from collections import Counter

# Set the base directory to scan
base_dir = "RA_tasks_2025"
formats = Counter()
unique_files = set()

for root, dirs, files in os.walk(base_dir):
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext:
            filename = file  # Only the filename, not the path
            if filename not in unique_files:
                formats[ext] += 1
                unique_files.add(filename)

# Map from filename to full path for printing
filename_to_fullpath = {}
for root, dirs, files in os.walk(base_dir):
    for file in files:
        filename = file
        if filename not in filename_to_fullpath:
            filename_to_fullpath[filename] = os.path.join(root, file)

print("File formats found in RA_tasks_2025 (unique files only):")
formats = dict(sorted(formats.items(), key=lambda item: item[1], reverse=True))
for ext, count in formats.items():
    print(f"{ext}: {count} unique files")

print("\n\n not processed PDFs:\n\n")
not_processed_pdfs = set()
import json
with open('results/processed_pdfs.json', 'r') as f:
    processed_pdfs = json.load(f)
processed_pdfs = processed_pdfs["processed_pdfs"]

# Extract only the filename from each processed PDF path
processed_pdf_filenames = set([os.path.basename(p.split("/")[-1]) for p in processed_pdfs])

not_processed_pdfs = set([f for f in unique_files if f.lower().endswith('.pdf')]) - processed_pdf_filenames
print("Not processed PDFs found in RA_tasks_2025:")
for filename in not_processed_pdfs:
    print(filename_to_fullpath.get(filename, filename))
print(f"\nTotal: {len(not_processed_pdfs)} unique not processed PDFs")

unprocessed_pdfs_paths = [filename_to_fullpath[filename] for filename in not_processed_pdfs if filename in filename_to_fullpath]

with open('unprocessed_pdfs.json', 'w') as f:
    json.dump(sorted(unprocessed_pdfs_paths), f, indent=2)

print("\n\nListing specific file formats (unique files only):\n\n")

zip_files = set()
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.lower().endswith('.zip'):
            zip_files.add(file)  # Only the filename, not the path
print(".zip files found in RA_tasks_2025:")
for filename in zip_files:
    print(filename_to_fullpath.get(filename, filename))
print(f"\nTotal: {len(zip_files)} unique .zip files")

xlsx_files = set()
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.lower().endswith('.xlsx'):
            xlsx_files.add(file)  # Only the filename, not the path
print(".xlsx files found in RA_tasks_2025:")
for filename in xlsx_files:
    print(filename_to_fullpath.get(filename, filename))
print(f"\nTotal: {len(xlsx_files)} unique .xlsx files")

msg_files = set()
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.lower().endswith('.msg'):
            msg_files.add(file)  # Only the filename, not the path
print(".msg files found in RA_tasks_2025:")
for filename in msg_files:
    print(filename_to_fullpath.get(filename, filename))
print(f"\nTotal: {len(msg_files)} unique .msg files")
