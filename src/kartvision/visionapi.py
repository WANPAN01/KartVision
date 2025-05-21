import io
from google.cloud import vision
from typing import List, Tuple, Optional
import time


class NotFoundResult(Exception):
    """OCR結果が見つからない例外"""
    def __str__(self) -> str:
        return "Flagの誤検知が発生しました"


def confirm_lines_interactively(lines: List[str]) -> List[str]:
    """
    行数が 12 でない場合、コンソール上でユーザーに補正を求め、最終的に 12 行に整える関数。
    ※ 表示はすべて1から始まる番号で行い、内部操作は0-basedに変換する。
    
    Args:
        lines (List[str]): OCRで検出されたテキスト行
        
    Returns:
        List[str]: 補正された12行のテキスト
    """
    attempts = 0
    max_attempts = 3
    
    while len(lines) != 12 and attempts < max_attempts:
        attempts += 1
        
        if len(lines) > 12:
            # 行数が12を超えている → 余分な行を削除してもらう
            print("\n警告: 行数が 12 行より多い、余分な文字があるかもしれません。")
            print("現在の行一覧:")
            for i, line in enumerate(lines, start=1):
                print(f"{i}: {line}")
            print(f"行数: {len(lines)} 行 (12 行に合わせる必要があります)")
            
            idx_str = input(
                "どれが余分ですか？(例: 1 だけなら '1', 複数なら '1,2' のようにカンマ区切りで) -> "
            )
            
            if not idx_str.strip():
                print("キャンセルしました。")
                break
                
            try:
                # ユーザー入力は1-basedなので、内部的に0-basedに変換する
                remove_indices = [int(x) - 1 for x in idx_str.split(",")]
                remove_indices.sort(reverse=True)  # 大きい番号から削除
                
                for idx in remove_indices:
                    if 0 <= idx < len(lines):
                        print(f"削除: {idx+1}:{lines[idx]}")
                        lines.pop(idx)
                    else:
                        print(f"無効な行番号です: {idx+1}")
            except ValueError:
                print("行番号の指定が無効です。もう一度やり直してください。")
                
        elif len(lines) < 12:
            # 行数が12未満 → 足りない行を追加してもらう
            print("\n警告: 行数が 12 行未満、集計には不足している可能性があります。")
            print("現在の行一覧:")
            for i, line in enumerate(lines, start=1):
                print(f"{i}: {line}")
            print(f"行数: {len(lines)} 行 (12 行に合わせる必要があります)")
            
            idx_str = input(
                "どこが足りないですか？(追加したい行の位置を1から指定、12位を追加したいなら 'end') -> "
            )
            
            if not idx_str.strip():
                print("キャンセルしました。")
                break
                
            if idx_str.strip().lower() == "end":
                insert_index = len(lines)
            else:
                try:
                    insert_index = int(idx_str) - 1  # 1-based → 0-based
                    insert_index = max(0, min(insert_index, len(lines)))  # 範囲内に収める
                except ValueError:
                    print("無効な入力です。キャンセルします。")
                    break
                    
            new_tag = input("名前はなんですか？ -> ")
            print(f"{insert_index+1} 番目に '{new_tag}' を追加します。")
            lines.insert(insert_index, new_tag)
    
    # 指定回数の試行後も12行にならなかった場合の自動補正
    if len(lines) > 12:
        print(f"警告: {attempts}回の試行後も行数が多すぎます。最初の12行のみを使用します。")
        lines = lines[:12]
    elif len(lines) < 12:
        print(f"警告: {attempts}回の試行後も行数が不足しています。空行を追加します。")
        while len(lines) < 12:
            lines.append(f"不明プレイヤー{len(lines)+1}")
            
    return lines


def result2ranking(retry_count: int = 3) -> List[Tuple[str, int]]:
    """
    OCR処理を行い、プレイヤー名とポイントのリストを返す
    
    Args:
        retry_count (int, optional): OCR処理の最大リトライ回数
        
    Returns:
        List[Tuple[str, int]]: (プレイヤー名, ポイント)のリスト
        
    Raises:
        NotFoundResult: OCR結果が取得できない場合
    """
    # 順位に応じた得点配分
    points_by_position = [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    
    for attempt in range(retry_count):
        try:
            # Google Cloud Visionクライアントの初期化
            client = vision.ImageAnnotatorClient()
            
            # 画像を読み込み
            with io.open("src/kartvision/static/cache/preprocess.png", "rb") as image_file:
                content = image_file.read()
                
            image = vision.Image(content=content)
            
            # OCR処理実行
            response = client.text_detection(image=image)
            
            # 結果がない場合はエラー
            if not response.text_annotations:
                print(f"OCR結果が空です。画像が読めませんでした。(試行 {attempt+1}/{retry_count})")
                if attempt < retry_count - 1:
                    time.sleep(1)  # リトライ前に少し待機
                    continue
                raise NotFoundResult()
                
            # 最初の要素が全テキスト
            raw_text = response.text_annotations[0].description
            lines = raw_text.split("\n")
            
            print("[DEBUG] OCR全文:")
            print(raw_text)
            print("[DEBUG] 行数:", len(lines))
            
            for i, line in enumerate(lines, start=1):
                print(f" {i}: '{line}'")
                
            # インタラクティブに12行に整える
            lines = confirm_lines_interactively(lines)
            
            # 12行になっていない場合は失敗
            if len(lines) != 12:
                print("ユーザー確認後も 12 行に満たないため、集計を中断します。")
                return []
                
            # 上位12位分のデータを組み合わせる
            needed_lines = lines[:12]
            return list(zip(needed_lines, points_by_position))
            
        except NotFoundResult:
            raise
        except Exception as e:
            print(f"OCR処理中にエラーが発生しました: {e} (試行 {attempt+1}/{retry_count})")
            if attempt < retry_count - 1:
                time.sleep(1)  # リトライ前に少し待機
                
    raise NotFoundResult()
