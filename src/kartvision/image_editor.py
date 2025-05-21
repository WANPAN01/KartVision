from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import os

def preprocess_image():
    """
    OCR用に画像の前処理を行う関数
    1. モノクロ化
    2. 明るさ調整
    3. メディアンフィルタ適用
    4. シャープネス調整
    5. 二値化
    6. 行区切り線の追加
    """
    # ファイルパスの設定
    input_path = "src/kartvision/static/cache/combined_image.png"
    output_path = "src/kartvision/static/cache/preprocess.png"
    
    try:
        # 画像が存在するか確認
        if not os.path.exists(input_path):
            print(f"エラー: 入力画像が見つかりません: {input_path}")
            return False
            
        # 画像を開く
        im = Image.open(input_path)
        
        # モノクロ変換
        im = im.convert("L")
        
        # 明るさ調整
        enhancer = ImageEnhance.Brightness(im)
        im = enhancer.enhance(0.8)
        
        # メディアンフィルタ適用（ノイズ除去）
        im = im.filter(ImageFilter.MedianFilter())
        
        # シャープネス調整
        enhancer = ImageEnhance.Sharpness(im)
        im = enhancer.enhance(2)
        
        # 二値化処理
        threshold = 128
        im = im.point(lambda p: 255 if p > threshold else 0)
        
        # 区切り線の追加
        draw = ImageDraw.Draw(im)
        img_width, img_height = im.size
        
        # 行数と線の位置計算
        num_lines = 11  # 12行のデータに対して11本の区切り線
        step = img_height // (num_lines + 1)
        line_positions = [step * i for i in range(1, num_lines + 1)]
        
        # 線を描画
        for y in line_positions:
            draw.line([(0, y), (img_width, y)], fill=255, width=10)
        
        # 画像の保存
        im.save(output_path)
        print(f"前処理済み画像に区切り線を追加して保存しました: {output_path}")
        return True
    except Exception as e:
        print(f"画像処理中にエラーが発生しました: {e}")
        return False