import urllib.request
import os
import shutil

# Download Bengali traineddata
url = 'https://github.com/tesseract-ocr/tessdata/raw/main/ben.traineddata'
local_file = os.path.join(os.environ.get('TEMP', '.'), 'ben.traineddata')

print('[1/3] Downloading ben.traineddata (12 MB)...')
urllib.request.urlretrieve(url, local_file)
print(f'[2/3] Downloaded to: {local_file}')

# Try to copy to Tesseract folder
target = r'C:\Program Files\Tesseract-OCR\tessdata\ben.traineddata'
try:
    shutil.copy2(local_file, target)
    print(f'[3/3] DONE! Copied to: {target}')
except PermissionError:
    print(f'[3/3] Permission denied. Manual copy needed.')
    print(f'Copy from: {local_file}')
    print(f'Copy to: {os.path.dirname(target)}')
