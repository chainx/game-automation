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
    item_images = partition_screenshot(screenshot, offset, sell_from_bottom_up)
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

def partition_screenshot(screenshot, offset=0, sell_from_bottom_up=True):
    item_images = []
    box_height = 28
    for n in range(8-offset):
        box = (0, box_height*n, 180, 30+box_height*n)
        cropped_screenshot = screenshot.crop(box)
        item_images.append(cropped_screenshot)
    
    if sell_from_bottom_up:
        return item_images[::-1]    
    return item_images

def is_not_black_image(image):
    stat = ImageStat.Stat(image)
    return sum(stat.sum) > 10000

def extract_count(screenshot, debug=False):
    n, count = 0, ''
    while 10*(n+.5) < screenshot.width:
        adjustment = 1 if n<3 else 0
        box = (10*n-1+adjustment, 0, 10*(n+1)+adjustment, 17)
        cropped_screenshot = screenshot.crop(box)
        if debug:
            cropped_screenshot.save(save_path/f'debug_{n}.png')
        if is_not_black_image(cropped_screenshot):
            text = pytesseract.image_to_string(cropped_screenshot, config=r'--psm 10 -c tessedit_char_whitelist=0123456789').replace('\n', '')
            if not text:
                text = pytesseract.image_to_string(cropped_screenshot, config=r'--psm 10').replace('\n', '')
                text = text if text.isdigit() else '0'
            count += text
        n += 1
    return int(count)