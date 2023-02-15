import subprocess
import os

def find_files(extension, directory):
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                file_paths.append(os.path.join(root, file))
    return file_paths

def pdfs_to_text(dir):
    pdf_paths = find_files('pdf', dir)
    for pdf_path in pdf_paths:
        cmd = 'pdftotext -layout {} {}.txt'.format(pdf_path, pdf_path)
        # shell_capture = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
