import pytesseract
from pathlib import Path
from PIL import Image, ImageStat
from fuzzywuzzy import fuzz

save_path = Path('Makai_Kingdom/Reference images')

items = [
    "Pumpkin",
    "Veggie Soup",
    "S. Short Cake",
    "Omelet",
    "Corn",
]

def keep_item(item_image, text, threshold=60):
    return [item for item in items if fuzz.ratio(text, item) >= threshold]

def find_items_to_sell(screenshot, offset=0, sell_from_bottom_up=True):
    item_images = partition_screenshot(screenshot, offset)
    if sell_from_bottom_up:
        item_images = item_images[::-1]
    items_kept, items_kept_indices = [], []
    for index, item_image in enumerate(item_images):
        item_image, has_stars = clean_image(item_image)
        extracted_text = pytesseract.image_to_string(item_image, config=r'--psm 7').strip()
        if (item_kept := keep_item(item_image, extracted_text)) or has_stars:
            items_kept_indices.append(index)
            items_kept += item_kept if not has_stars else ['Stars']
    return items_kept, items_kept_indices

def clean_image(item_image):
    data = item_image.load()
    yellow_count = 0
    for x in range(item_image.width):
        for y in range(item_image.height):
            r, g, b = data[x, y]
            dist_from_white = ((255-r)**2+(255-g)**2+(255-b)**2)
            dist_from_yellow = ((255-r)**2+(255-g)**2+(0-b)**2)
            if dist_from_white > 250**2:
                data[x, y] = (0, 0, 0)
            elif dist_from_yellow < 140**2:
                yellow_count+=1
    return item_image, yellow_count > 10

def partition_screenshot(screenshot, offset=0, box_height=28):
    item_images = []
    for n in range(8-offset):
        box = (0, box_height*n, 180, box_height*(n+1)+2)
        cropped_screenshot = screenshot.crop(box)
        item_images.append(cropped_screenshot)    
    return item_images