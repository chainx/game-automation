import pytesseract
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
    # try:
    #     extracted_text = [item for item in items if item in extracted_text][0]
    # except:
    #     pass # print(f'No match found for {extracted_text}')
    print("Extracted text using OCR:", extracted_text)

# import torch
# import clip

# texts = items 
# texts += [text + " with a star next to it" for text in items]
# texts += [text + " with three stars next to it" for text in items]
# texts += ["The text says " + text for text in items]
# texts += ["The text reads " + text for text in items]
# texts += ["The image contains the text " + text for text in items]
# texts += ["This is a " + text for text in items]

# device = "cuda" if torch.cuda.is_available() else "cpu"
# model, preprocess = clip.load("ViT-B/32", device=device)

# # Preprocess the extracted text as an image
# image = preprocess(Image.fromarray(pytesseract.image_to_boxes(image))).unsqueeze(0).to(device)
# # Tokenize the text prompts
# text_tokens = clip.tokenize(texts).to(device)

# # Perform inference
# with torch.no_grad():
#     image_features = model.encode_image(image)
#     text_features = model.encode_text(text_tokens)
#     logits_per_image, logits_per_text = model(image, text_tokens)
#     probs = logits_per_image.softmax(dim=-1).cpu().numpy()

# # Output the most likely text
# most_likely_text = texts[probs.argmax()]
# print("Most likely text:", most_likely_text)
# print("Probabilities:", probs)
