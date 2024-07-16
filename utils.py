import requests
import os

def download_images(url, path="output/img_files"):
    if not os.path.exists(path):
        os.makedirs(path)
    filename = url.split('/')[-1]
    filepath = os.path.join(path, filename)
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(response.content)
    return filename

