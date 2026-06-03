import cv2
import numpy as np

def extract_characters_from_mask(mask_path):
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bounding_boxes = [cv2.boundingRect(c) for c in contours]
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])
    
    extracted_chars = []
    
    for x, y, w, h in bounding_boxes:
        if w < 5 or h < 5:
            continue
            
        cropped_char = mask[y-5:y+h+5, x-5:x+w+5]
        extracted_chars.append(cropped_char)
        
    return extracted_chars

if __name__ == "__main__":
    mask_path = "dataset/masks/Y1X7PK_mask.png"
    characters = extract_characters_from_mask(mask_path)
    
    for i, char in enumerate(characters):
        cv2.imwrite(f"extracted_chars/{i}.png", char)