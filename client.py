import requests
import time
import os
import subprocess

SERVER_URL = os.getenv('SERVER_URL')
SLIDES_DIR = os.getenv('SLIDES_DIR')

if not os.path.exists(SLIDES_DIR):
    os.makedirs(SLIDES_DIR)

def fetch_slides():
    print(f'Fetching slides from {SERVER_URL}')
    response = requests.get(f'{SERVER_URL}/slides')
    return response.json()

def download_slide(filename):
    response = requests.get(f'{SERVER_URL}/slides/{filename}', stream=True)
    with open(os.path.join(SLIDES_DIR, filename), 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def display_slides(slides, delay):
    slide_paths = [os.path.join(SLIDES_DIR, slide) for slide in slides]
    return subprocess.Popen(['feh', '-Y', '-x', '-q', '-D', str(delay/1000), '-F', '-Z'] + slide_paths)

def main():
    local_slides = set()
    feh_process = None
    current_delay = None

    while True:
        try:
            data = fetch_slides()
            slides_changed = False
            delay_changed = data['delay'] != current_delay

            for slide in data['slides']:
                if slide not in local_slides:
                    download_slide(slide)
                    local_slides.add(slide)
                    slides_changed = True

            # Remove any local slides that are no longer in the server's list
            for slide in list(local_slides):
                if slide not in data['slides']:
                    os.remove(os.path.join(SLIDES_DIR, slide))
                    local_slides.remove(slide)
                    slides_changed = True

            if slides_changed or delay_changed:
                if feh_process:
                    feh_process.terminate()
                feh_process = display_slides(data['slides'], data['delay'])
                current_delay = data['delay']
                print(f"Slideshow updated. Delay: {current_delay}ms")
            else:
                time.sleep(5)  # Wait 5 seconds before checking for updates again
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)  # Wait 10 seconds before retrying in case of error

if __name__ == '__main__':
    main()