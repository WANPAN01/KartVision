import io
from google.cloud import vision
from typing import List, Tuple


class NotFoundResult(Exception):
    def __str__(self) -> str:
        return "Flagの誤検知が発生しました"


def confirm_lines_interactively(lines: List[str]) -> List[str]:
    """
    行数が 12 でない場合、コンソール上でユーザーに補正を求め、最終的に 12 行に整える関数。
    ※ 表示はすべて1から始まる番号で行い、内部操作は0-basedに変換する。
    """
    while len(lines) != 12:
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
                remove_indices.sort(reverse=True)
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
                    insert_index = int(idx_str) - 1
                    if insert_index < 0:
                        insert_index = 0
                    if insert_index > len(lines):
                        insert_index = len(lines)
                except ValueError:
                    print("無効な入力です。キャンセルします。")
                    break
            new_tag = input("名前はなんですか？ -> ")
            print(f"{insert_index+1} 番目に '{new_tag}' を追加します。")
            lines.insert(insert_index, new_tag)

    return lines


def result2ranking() -> List[Tuple[str, int]]:
    points_by_position = [15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    client = vision.ImageAnnotatorClient()
    with io.open("src/kartvision/static/cashe/preprocess.png", "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)

    if not response.text_annotations:
        print("OCR結果が空です。画像が読めませんでした。")
        return []

    raw_text = response.text_annotations[0].description
    lines = raw_text.split("\n")

    print("[DEBUG] OCR全文:")
    print(raw_text)
    print("[DEBUG] 行数:", len(lines))
    for i, line in enumerate(lines, start=1):
        print(f"  {i}: '{line}'")

    # インタラクティブに 12 行に整える
    lines = confirm_lines_interactively(lines)

    # もし最終的に 12 行にならなかったら空リストを返す
    if len(lines) != 12:
        print("ユーザー確認後も 12 行に満たないため、集計を中断します。")
        return []

    # 12行を使用
    needed_lines = lines[:12]

    return list(zip(needed_lines, points_by_position))
