import os
import pyautogui
from PIL import Image
from typing import List, Dict
import datetime


class Screenshot_Manager:
    def __init__(self) -> None:
        """
        スクリーンショット管理クラスの初期化
        必要なディレクトリ構造を作成する
        """
        # 必要なディレクトリの作成
        static_dir = "src/kartvision/static"
        if not os.path.isdir(static_dir):
            os.makedirs(static_dir, exist_ok=True)
        
        history_dir = os.path.join(static_dir, "history")
        if not os.path.isdir(history_dir):
            os.makedirs(history_dir, exist_ok=True)
            
        cache_dir = os.path.join(static_dir, "cache")
        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            
        self.screenshot_filename = None
        
    def screenshot(self) -> str:
        """
        画面全体のスクリーンショットを撮影し保存する
        
        Returns:
            str: 保存されたスクリーンショットのファイルパス
        """
        now = datetime.datetime.now()
        self.screenshot_filename = f"src/kartvision/static/history/screenshot_{now.strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(self.screenshot_filename)
            print(f"スクリーンショットを保存しました: {self.screenshot_filename}")
            return self.screenshot_filename
        except Exception as e:
            print(f"スクリーンショット取得中にエラーが発生しました: {e}")
            return None
            
    def clip_and_combine_screenshot(self, region: List[int]) -> bool:
        """
        スクリーンショットから指定された領域を抽出し、縦に結合して保存する
        
        Args:
            region (List[int]): [x1, y1, x2, y2] 形式の領域指定
            
        Returns:
            bool: 処理が成功したかどうか
        """
        output_filename = "src/kartvision/static/cache/combined_image.png"
        
        try:
            if not self.screenshot_filename:
                print("エラー: スクリーンショットが取得されていません")
                return False
                
            # 対象領域を計算
            regions = get_regions(region)
            
            # 画像を開いて指定領域を切り抜き結合
            with Image.open(self.screenshot_filename) as img:
                cropped_images = [img.crop(r) for r in regions]
                total_height = sum(cropped.height for cropped in cropped_images)
                max_width = max(cropped.width for cropped in cropped_images)
                
                combined_image = Image.new("RGB", (max_width, total_height))
                y_offset = 0
                
                for cropped in cropped_images:
                    combined_image.paste(cropped, (0, y_offset))
                    y_offset += cropped.height
                    
                combined_image.save(output_filename)
                print(f"結合された画像を保存しました: {output_filename}")
                return True
        except Exception as e:
            print(f"画像結合中にエラーが発生しました: {e}")
            return False


def get_screenshot() -> List[str]:
    """
    保存されているスクリーンショットのリストを取得する
    
    Returns:
        List[str]: スクリーンショットのファイルパスリスト（日付順）
    """
    directory = "src/kartvision/static/history"
    if not os.path.exists(directory):
        return []
        
    images = ["history/" + f for f in os.listdir(directory) if f.endswith(".png")]
    images.sort(
        reverse=True,
        key=lambda x: os.path.getmtime(os.path.join(directory, x.split("history/")[1])),
    )
    return images


def get_screenshot_by_date() -> Dict[str, List[str]]:
    """
    日付ごとにグループ化されたスクリーンショットのリストを取得する
    
    Returns:
        Dict[str, List[str]]: 日付をキー、画像パスのリストを値とする辞書
    """
    directory = "src/kartvision/static/history"
    if not os.path.exists(directory):
        return {}
        
    images = ["history/" + f for f in os.listdir(directory) if f.endswith(".png")]
    images.sort(
        reverse=True,
        key=lambda x: os.path.getmtime(os.path.join(directory, x.split("history/")[1])),
    )
    
    images_by_date = {}
    for image in images:
        filename = image.split("/")[-1]
        date_time_str = filename.replace("screenshot_", "").replace(".png", "")
        date_part = date_time_str.split("_")[0]
        
        if date_part not in images_by_date:
            images_by_date[date_part] = []
            
        images_by_date[date_part].append(image)
        
    return images_by_date


def get_regions(region: List[int]) -> List[List[int]]:
    """
    マリオカートの結果表示スクリーンから各プレイヤー行の座標を計算する
    
    Args:
        region (List[int]): 全体の領域 [x1, y1, x2, y2]
        
    Returns:
        List[List[int]]: 各プレイヤー行の座標リスト
    """
    result_ratio = [10, 1]  # プレイヤー行と区切り行の比率
    region_len = region[3] - region[1]
    
    # 必要な単位長さを計算
    num = result_ratio[0] * 12 + result_ratio[1] * 11  # 12プレイヤー + 11区切り
    unit_len = region_len / num
    
    regions = []
    for i in range(12):
        # 各プレイヤー行の座標を計算
        y_start = region[1] + (i * (result_ratio[0] + result_ratio[1])) * unit_len
        y_end = y_start + result_ratio[0] * unit_len
        
        regions.append([
            region[0],  # x開始
            y_start,    # y開始
            region[2],  # x終了
            y_end       # y終了
        ])
    
    return regions
