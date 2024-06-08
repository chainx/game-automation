import pytesseract
import os
from pathlib import Path
from PIL import Image
from fuzzywuzzy import fuzz

items = [
    "Pumpkin",
    "Veggie Soup",
    "S. Short Cake",
    "Omelet",
    "Corn",
]

def keep_item(text, threshold=60):
    return [item for item in items if fuzz.ratio(text, item) >= threshold]

def find_items_to_sell(screenshot, offset=0, sell_from_bottom_up=True):
    screenshot = clean_screenshot(screenshot)
    item_images = partition_screenshot(screenshot, offset, sell_from_bottom_up)
    
    items_kept, items_kept_indices = [], []
    for index, item_image in enumerate(item_images):
        extracted_text = pytesseract.image_to_string(item_image).strip()
        if item_kept := keep_item(extracted_text):
            items_kept_indices.append(index)
            items_kept += item_kept
    return items_kept, items_kept_indices

def clean_screenshot(screenshot):
    data = screenshot.load()
    for x in range(screenshot.width):
        for y in range(screenshot.height):
            r, g, b = data[x, y]
            dist_from_white = ((255-r)**2+(255-g)**2+(255-b)**2)**0.5
            if  dist_from_white > 250:
                data[x, y] = (0, 0, 0)
    
    return screenshot

def partition_screenshot(screenshot, offset, sell_from_bottom_up):
    item_images = []
    box_height = 30
    for n in range(8-offset):
        box = (35, 30+box_height*n, 180, 60+box_height*n)
        cropped_screenshot = screenshot.crop(box)
        item_images.append(cropped_screenshot)
    
    if sell_from_bottom_up:
        return item_images[::-1]    
    return item_images
