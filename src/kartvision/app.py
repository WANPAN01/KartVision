import json
import os
from time import sleep
from datetime import datetime   
from threading import Thread
import shutil

from flask import render_template, request, jsonify
from pyautogui import locateOnScreen, ImageNotFoundException

from visionapi import result2ranking, NotFoundResult
from screenshot import get_screenshot_by_date, Screenshot_Manager
import image_editor
from user import create_teams_with_tags
from server import KartFlask


# --- 設定関連 ---
def load_region():
    """
    config.json があれば REGION を読み込み、なければデフォルトの値を返す
    """
    default_region = [1520, 206, 2125, 1596]
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("REGION", default_region)
    return default_region


def load_config():
    """
    設定をまとめて読み込み、デフォルト値と合わせて返す
    """
    config = {
        "region": load_region(),
        "port": 8888,
        "flag_confidence": 0.8,
        "similarity_threshold": 0.6
    }
    return config


# --- 初期化 ---
config = load_config()
REGION = config["region"]
print(f"使用するREGION: {REGION}")

screenshot_manager = Screenshot_Manager()
app = KartFlask(__name__)


# --- Flask ルート ---
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/result")
def results():
    data = app.high_score_list()
    print(f"Resultデータ: {data}")
    return render_template("result.html", data=data)


@app.route("/history")
def history():
    images_by_date = get_screenshot_by_date()
    dates = sorted(images_by_date.keys(), reverse=True)
    return render_template("history.html", images_by_date=images_by_date, dates=dates)

@app.route("/api/delete_image", methods=["POST"])
def delete_image():
    try:
        data = request.get_json(force=True)
        rel_path = data.get('image_path')          # 例: 'history/screenshot_202505.png'
        if not rel_path:
            return jsonify(success=False, message="画像パスがありません"), 400

        base_dir   = os.path.abspath(os.path.dirname(__file__))
        static_dir = os.path.join(base_dir, 'static')
        abs_path   = os.path.join(static_dir, rel_path)   # ← ② static 直下へ解決

        # セキュリティチェック: static 内に収まっているか
        if os.path.commonpath([abs_path, static_dir]) != static_dir:
            return jsonify(success=False, message="無効なパスです"), 403

        if os.path.isfile(abs_path):
            # --- ゴミ箱へ移動 or 物理削除 ---
            trash_dir = os.path.join(static_dir, 'trash')
            os.makedirs(trash_dir, exist_ok=True)
            shutil.move(abs_path, os.path.join(trash_dir, os.path.basename(abs_path)))
            # os.remove(abs_path)  # ← 完全削除ならこちら

            # ログ書き込み
            with open(os.path.join(base_dir, 'deleted_images.log'), 'a') as f:
                f.write(f"{rel_path} deleted at {datetime.now():%Y-%m-%d %H:%M:%S}\n")

            return jsonify(success=True), 200

        return jsonify(success=False, message="ファイルが見つかりません"), 404
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    
@app.route("/edit")
def edit():
    data = app.high_score_list()
    return render_template("edit.html", data=data)


@app.route("/api/data")
def get_data():
    return jsonify(app.high_score_list())


@app.route("/api/edit_tag", methods=["POST"])
def edit_tag():
    """
    タグ更新API
    リクエストJSON例: {"tag": "旧タグ", "new_tag": "新タグ"}
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "JSONデータが見つかりません"}), 400
        
    current_tag = data.get("tag")
    new_tag = data.get("new_tag")
    if not current_tag or not new_tag:
        return jsonify({"status": "error", "message": "タグ情報が不足しています"}), 400

    for team in app.teams:
        if team.tag == current_tag:
            team.tag = new_tag
            print(f"タグ更新: {current_tag} -> {new_tag}")
            return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "指定されたタグが見つかりませんでした"}), 404


@app.route("/api/edit_points", methods=["POST"])
def edit_points():
    """
    点数更新およびチーム統合API
    リクエストJSON例（直接点数編集）: {"tag": "チームタグ", "points": 新合計点}
    リクエストJSON例（統合）: {"tag": "統合元タグ", "target_tag": "統合先タグ"}
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "JSONデータが見つかりません"}), 400
        
    tag = data.get("tag")
    if not tag:
        return jsonify({"status": "error", "message": "タグ情報が不足しています"}), 400
        
    new_points = data.get("points", None)
    target_tag = data.get("target_tag", None)

    # --- チーム統合 ---
    if target_tag:
        source_team = None
        dest_team = None
        for team in app.teams:
            if team.tag == tag:
                source_team = team
            elif team.tag == target_tag:
                dest_team = team
        if not source_team or not dest_team:
            return jsonify({"status": "error", "message": "指定されたタグが見つかりませんでした"}), 404

        dest_team.users.extend(source_team.users)
        app.teams = [t for t in app.teams if t.tag != tag]
        print(f"統合完了: {tag} -> {target_tag}")
        return jsonify({"status": "success"})

    # --- 直接点数編集 ---
    elif new_points is not None:
        for team in app.teams:
            if team.tag == tag:
                # チームの合計点は、各ユーザーの合計点の合計で計算する
                current_total = sum(user.sum_points() for user in team.users)
                diff = new_points - current_total
                num_members = len(team.users)
                if num_members > 0:
                    adjustment = diff // num_members
                    remainder = diff % num_members
                    for i, user in enumerate(team.users):
                        user.points[-1] += adjustment
                        if i < remainder:
                            user.points[-1] += 1
                    print(f"点数更新: {tag} の合計点 {current_total} -> {new_points}")
                    return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "指定されたタグが見つかりませんでした"}), 404
    else:
        return jsonify({"status": "error", "message": "更新内容が不正です"}), 400


# --- フラグ検出 & OCR 更新ループ ---
def run_flag_detection(group_num, tag_positions):
    """
    tag_positions: 集計に使うタグの種類（例: ["prefix"] または ["prefix", "suffix"]）
    """
    flag_image = "src/kartvision/static/images/flag_trigger.png"
    group_num_int = int(group_num)
    is_init = True

    while True:
        try:
            sleep(0.1)
            print("待機中...")
            try:
                locateOnScreen(flag_image, confidence=config["flag_confidence"])
            except ImageNotFoundException:
                continue

            print("日本国旗検出: スクリーンショット取得前に待機します...")
            sleep(1)  # 画面が完全に表示されるまで少し待機
            
            # スクリーンショット取得と処理
            screenshot_manager.screenshot()
            screenshot_manager.clip_and_combine_screenshot(REGION)
            image_editor.preprocess_image()

            try:
                ranking = result2ranking()
                print("OCR結果:", ranking)
            except NotFoundResult as e:
                print(f"エラー: {e}")
                continue
            except Exception as e:
                print(f"予期せぬエラー: {e}")
                continue

            if is_init:
                print("初回: チームを設定中...")
                teams = create_teams_with_tags(ranking, group_num=group_num_int, tag_positions=tag_positions)
                app.set_teams(teams)
                is_init = False
            else:
                print("更新: ユーザー情報を更新します...")
                app.update(ranking)

            # 集計結果表示
            for team in app.teams:
                print(team)
            print("合計ポイント:")
            for item in app.high_score_list():
                print(f"{item['tag']} - {item['sum_points']}")
                
            # 次の検出までの待機時間
            sleep(10)
        except Exception as e:
            print(f"検出ループ内でエラーが発生しました: {e}")
            sleep(5)  # エラー時の短い待機


# --- エントリーポイント ---
if __name__ == "__main__":
    try:
        # 対戦形式の選択
        group_num = None
        valid_options = ["2", "3", "4", "6"]
        while group_num not in valid_options:
            group_num = input("対戦形式はどれですか？ (2v2 -> 2, 3v3 -> 3, 4v4 -> 4, 6v6 -> 6): ")
            if group_num not in valid_options:
                print("無効な入力です。再入力してください。")
        
        # タグの集計方法を選択
        tag_mode = None
        while tag_mode not in ["1", "2"]:
            tag_mode = input("タグの集計方法を指定してください： 1) 前タグのみ, 2) 前後タグ: ")
            if tag_mode not in ["1", "2"]:
                print("無効な入力です。")
                
        tag_positions = ["prefix"] if tag_mode == "1" else ["prefix", "suffix"]

        # 検出スレッドの開始
        flag_thread = Thread(target=run_flag_detection, args=(group_num, tag_positions))
        flag_thread.daemon = True
        flag_thread.start()
        
        # Webサーバーの開始
        app.run(host="0.0.0.0", port=config["port"], debug=False)
    except KeyboardInterrupt:
        print("\nプログラムを終了します。")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")