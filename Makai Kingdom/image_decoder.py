import pytesseract
import os
from pathlib import Path
from PIL import Image

save_path = Path('Makai Kingdom/Reference images')

items = [
    "Pine Tree",
    "Small Flower",
    "Corn",
    "Veggie Soup",
    "Pumpkin",
    "Leather Armour"
]

for n in range(8):
    image = Image.open(save_path / f'cropped_output_{n}.png')
    extracted_text = pytesseract.image_to_string(image).strip()
    print("Extracted text using OCR:", extracted_text)
