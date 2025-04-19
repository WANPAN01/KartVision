from PIL import Image, ImageEnhance, ImageFilter, ImageDraw

def preprocess_image():
    im = Image.open("src/kartvision/static/cashe/combined_image.png")
    im = im.convert("L")
    enhancer = ImageEnhance.Brightness(im)
    im = enhancer.enhance(0.8)
    im = im.filter(ImageFilter.MedianFilter())
    enhancer = ImageEnhance.Sharpness(im)
    im = enhancer.enhance(2)
    threshold = 128
    im = im.point(lambda p: 255 if p > threshold else 0)
    
    draw = ImageDraw.Draw(im)
    img_width, img_height = im.size
    num_lines = 11
    line_positions = []
    step = img_height // (num_lines + 1)

    for i in range(1, num_lines):
        y = step * i
        line_positions.append(y)

    for y in line_positions:
        draw.line([(0, y), (img_width, y)], fill=255, width=10)  # ここでは黒線(width=5)

    im.save("src/kartvision/static/cashe/preprocess.png")
    print("前処理済み画像に区切り線を追加して保存しました。")
