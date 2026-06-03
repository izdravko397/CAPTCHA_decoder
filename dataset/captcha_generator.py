import os
import random
import string
import glob
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
HEIGHT = 70
ALLOWED_CHARS = string.ascii_uppercase + string.digits
FONTS_DIR = "dataset/fonts" 

def draw_complex_noise(draw_obj, width):
    num_boxes = random.randint(6, 12)
    for _ in range(num_boxes):
        x1 = random.randint(-10, width - 30)
        y1 = random.randint(-10, HEIGHT - 20)
        x2 = x1 + random.randint(30, 80)
        y2 = y1 + random.randint(20, 45)
        
        gray_val = random.randint(100, 210)
        alpha = random.randint(40, 90) 
        rect_color = (gray_val, gray_val, gray_val, 255)
        
        draw_obj.rectangle([x1, y1, x2, y2], fill=rect_color, outline=None)
        draw_obj.rectangle([x1, y1, x2, y2], fill=None, outline=(gray_val - 20, gray_val - 20, gray_val - 20, alpha), width=random.randint(1, 2))

    num_lines = random.randint(4, 8)
    for _ in range(num_lines):
        x = random.randint(10, width - 10)
        gray_val = random.randint(70, 200)
        draw_obj.line([(x, 0), (x, HEIGHT)], fill=(gray_val, gray_val, gray_val, 255), width=random.randint(1, 3))

def generate_advanced_pair(text, num=1):
    available_fonts = glob.glob(os.path.join(FONTS_DIR, "*.ttf"))
    if not available_fonts:
        print(f"Грешка: Няма .ttf файлове в папка {FONTS_DIR}")
        return None, None

    char_images = []
    total_width = 0
    margin = 15  

    for char_idx, char in enumerate(text):
        font_path = random.choice(available_fonts)
        font_size = random.randint(38, 46)
        font = ImageFont.truetype(font_path, font_size)
        
        char_color = (255, 255, 255, 255) if random.random() < 0.6 else (0, 0, 0, 255)
        
        bbox = font.getbbox(char)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        
        if char == " ":
            w = 15
            char_images.append(None)
            total_width += w
            continue

        pad = 10
        temp_img = Image.new("RGBA", (w + pad, h + pad), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        temp_draw.text((pad // 2 - bbox[0], pad // 2 - bbox[1]), char, fill=char_color, font=font)

        clean_char_mask = temp_img.split()[3]
        straight_char_img = Image.new("L", temp_img.size, color=0)
        white_block = Image.new("L", temp_img.size, 255)
        straight_char_img.paste(white_block, (0, 0), clean_char_mask)
        
        clean_filename = f"sample{num}_idx{char_idx}_{char}.png"
        straight_char_img.save(f"dataset/model_3/{clean_filename}")
        # ===================================================================
        
        angle = random.randint(-25, 25)
        rotated_char = temp_img.rotate(angle, resample=Image.BICUBIC, expand=1)
        
        char_images.append((rotated_char, char_color, char, angle))
        total_width += (rotated_char.width - 6)

    dynamic_width = total_width + (margin * 2)

    captcha_img = Image.new("RGBA", (dynamic_width, HEIGHT), color=(200, 200, 200, 255))
    mask_img = Image.new("L", (dynamic_width, HEIGHT), color=0)

    draw_captcha = ImageDraw.Draw(captcha_img, "RGBA")
    draw_mask = ImageDraw.Draw(mask_img)

    draw_complex_noise(draw_captcha, dynamic_width)

    current_x = margin

    for item in char_images:
        if item is None:
            current_x += 15
            continue
            
        rotated_char, char_color, char, angle = item
        
        y_pos = (HEIGHT - rotated_char.height) // 2 + random.randint(-6, 6)
        
        captcha_img.alpha_composite(rotated_char, (current_x, y_pos))
        
        char_mask = rotated_char.split()[3]
        white_block = Image.new("L", rotated_char.size, 255)
        mask_img.paste(white_block, (current_x, y_pos), char_mask)

        single_char_mask = Image.new("L", (rotated_char.width, rotated_char.height), color=0)
        single_char_mask.paste(white_block, (0, 0), char_mask)
        char_filename = f"{char}_angle_{angle}_{num}.png"
        single_char_mask.save(f"dataset/model_2/{char_filename}")

        current_x += (rotated_char.width - 6)

    final_captcha = Image.new("RGB", captcha_img.size, (110, 110, 110))
    final_captcha.paste(captcha_img, mask=captcha_img.split()[3])

    return final_captcha, mask_img

if __name__ == "__main__":
    num_samples = int(input("Input number of CAPTCHA samples to generate: "))
    start_num = int(input("Input starting number for naming files (default is 1): ") or 1)

    os.makedirs("dataset/model_1", exist_ok=True)
    os.makedirs("dataset/model_1/images", exist_ok=True)
    os.makedirs("dataset/model_1/masks", exist_ok=True)
    os.makedirs("dataset/model_2", exist_ok=True)
    os.makedirs("dataset/model_3", exist_ok=True)


    success_count = 0
    for num in range(start_num, start_num + num_samples):
        num_symbols = random.randint(4, 7)
        random_text = ''.join(random.choices(ALLOWED_CHARS, k=num_symbols))

        captcha = None
        captcha, mask = generate_advanced_pair(random_text, num=num)
        
        if captcha:
            safe_name = random_text.replace(" ", "_")
            captcha.save(f"dataset/model_1/images/{safe_name}.png")
            mask.save(f"dataset/model_1/masks/{safe_name}_mask.png")

            success_count += 1
    
    print(f"Successfully generated CAPTCHA samples: {success_count}")