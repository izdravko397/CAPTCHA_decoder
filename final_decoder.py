import string
import glob
import cv2
import os
import re
import numpy as np
import tensorflow as tf 
import matplotlib.pyplot as plt

def rounding_pixels(mask, threshold=0.5):
    mask_cpy = mask.copy()
    mask_cpy[mask_cpy < threshold] = 0.0
    mask_cpy[mask_cpy >= threshold] = 1.0
    return mask_cpy.astype(np.uint8)

def extract_characters_from_mask(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bounding_boxes = [cv2.boundingRect(c) for c in contours]
    bounding_boxes = sorted(bounding_boxes, key=lambda b: b[0])
    
    extracted_chars = []
    h_mask, w_mask = mask.shape
    
    for x, y, w, h in bounding_boxes:
        if w < 5 or h < 5:
            continue
            
        y_start = np.clip(y - 5, 0, h_mask)
        y_end = np.clip(y + h + 5, 0, h_mask)
        x_start = np.clip(x - 5, 0, w_mask)
        x_end = np.clip(x + w + 5, 0, w_mask)
        
        cropped_char = mask[y_start:y_end, x_start:x_end]
        extracted_chars.append(cropped_char)
        
    return extracted_chars

def captcha_decoder(captcha_path):
    model_1 = tf.keras.models.load_model("1_background_remover/models/best_unet_model.keras")
    model_2 = tf.keras.models.load_model("2_symbol_rotation/models/best_rotation_model.keras")
    model_3 = tf.keras.models.load_model("3_symbol_classifier/models/sym_clf_model.keras")

    ALLOWED_CHARS = string.ascii_uppercase + string.digits
    INDEX_TO_CLASS = {idx: char for idx, char in enumerate(ALLOWED_CHARS)}

    img_bgr = cv2.imread(captcha_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (256, 64))
    img = img_resized.astype(np.float32) / 255.0
    img = img[np.newaxis, ...]

    predicted_mask = model_1.predict(img, verbose=0)[0]
    if len(predicted_mask.shape) == 3:
        predicted_mask = predicted_mask[:, :, 0]
    rounded_mask = rounding_pixels(predicted_mask, threshold=0.1)

    extracted_chars = extract_characters_from_mask(rounded_mask)
    decoded_captcha = ""

    fig, ax = plt.subplots(2, len(extracted_chars) + 1, figsize=(15, 5))

    for i, char in enumerate(extracted_chars):
        char_resized = cv2.resize(char * 255, (36, 52)).astype(np.float32)
        char_tensor = rounding_pixels(char_resized[np.newaxis, ..., np.newaxis] / 255.0)

        predicted_norm_angle = model_2.predict(char_tensor, verbose=0)[0][0]
        predicted_angle = predicted_norm_angle * 25.0

        ax[0, i].imshow(char_tensor[0, :, :, 0], cmap="gray")
        ax[0, i].set_title(f"Angle: {predicted_angle:.1f}")

        M = cv2.getRotationMatrix2D((18, 26), -predicted_angle, 1.0)
        rotated_char = cv2.warpAffine(char_resized, M, (36, 52), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        rotated_char_tensor = rounding_pixels(rotated_char[np.newaxis, ..., np.newaxis] / 255.0)

        symbol_pred = np.argmax(model_3.predict(rotated_char_tensor, verbose=0))
        decoded_captcha += INDEX_TO_CLASS[int(symbol_pred)]

        ax[1, i].imshow(rotated_char_tensor[0, :, :, 0], cmap="gray")
        ax[1, i].set_title(INDEX_TO_CLASS[int(symbol_pred)])    
        
        ax[1, i].axis("off")
        ax[0, i].axis("off")

    print("Decoded CAPTCHA:", decoded_captcha)
    ax[0, -1].imshow(img[0])
    ax[0, -1].set_title(f"Predicted: {decoded_captcha}")

    ax[0, -1].axis("off")
    ax[1, -1].axis("off")
    
    plt.show()

    return decoded_captcha

if __name__ == "__main__":
    paths = glob.glob("dataset/model_1/images/*")
    idx = np.random.randint(0, len(paths))

    img_path = paths[idx]

    captcha_code = re.sub(r"\.png", "", os.path.basename(img_path))
    print(f"Decoding CAPTCHA from image: {captcha_code}")
    decoded_captcha = captcha_decoder(img_path)