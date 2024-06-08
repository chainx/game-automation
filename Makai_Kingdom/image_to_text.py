import pytesseract
import os
from pathlib import Path
from PIL import Image

items = [
    "Pine Tree",
    "Small Flower",
    "Corn",
    "Veggie Soup",
    "Pumpkin",
    "Leather Armour"
]

def find_items_to_sell(screenshot):
    items_to_sell = []

    screenshot = clean_screenshot(screenshot)
    item_images = partition_screenshot(screenshot)
    for item_image in item_images:
        extracted_text = pytesseract.image_to_string(item_image).strip()
        items_to_sell.append(extracted_text)

    return items_to_sell

def clean_screenshot(screenshot):
    data = screenshot.load()
    for x in range(screenshot.width):
        for y in range(screenshot.height):
            r, g, b = data[x, y]
            dist_from_white = ((255-r)**2+(255-g)**2+(255-b)**2)**0.5
            if  dist_from_white > 250:
                data[x, y] = (0, 0, 0)
    
    return screenshot

def partition_screenshot(screenshot):
    item_images = []
    box_height = 30
    for n in range(8):
        box = (35, 30+box_height*n, 180, 60+box_height*n)
        cropped_screenshot = screenshot.crop(box)
        item_images.append(cropped_screenshot)
    
    return item_images
