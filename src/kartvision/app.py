from flask import render_template, Flask
import visionapi
import threading
import pyautogui
from time import sleep
import screenshot
import image_editor
import analyzer
from threading import Lock
import time

data_lock = Lock()
data = []
all_users_lock = Lock()
all_users = {}

screenshot_manager = screenshot.Screenshot_Manager()  # グローバルでインスタンスを一度だけ作成

app = Flask(__name__)

@app.route("/")
def results():
    with data_lock:
        return render_template("result.html", data=data)

@app.route("/history")
def history():
    images_by_date = screenshot.get_screenshot_by_date()
    dates = sorted(images_by_date.keys(), reverse=True)
    return render_template("history.html", images_by_date=images_by_date, dates=dates)

def run():
    global data, all_users
    # 設定
    wait_time_before_screenshot = 0.3
    flag_image = "src/kartvision/static/images/flag_trigger.png"
    
    running = True
    while running:
        sleep(0.1)
        print("待機中...")
        try:
            location = pyautogui.locateOnScreen(flag_image, confidence=0.7)
        except pyautogui.ImageNotFoundException:
            continue

        if location:
            print("日本国旗が見つかりました。スクリーンショットを撮る前に待機します...")
            sleep(wait_time_before_screenshot)
            screenshot_manager.screenshot()

            regions = [
                (1520, 204, 2125, 309), (1520, 321, 2125, 426), 
                (1520, 438, 2125, 543), (1520, 555, 2125, 660), 
                (1520, 672, 2125, 777), (1520, 789, 2125, 894), 
                (1520, 906, 2125, 1011), (1520, 1023, 2125, 1128),
                (1520, 1140, 2125, 1245), (1520, 1257, 2125, 1362),
                (1520, 1374, 2125, 1479), (1520, 1491, 2125, 1596)
            ]
            
            screenshot_manager.clip_and_combine_screenshot(
                regions, "src/kartvision/static/cashe/combined_image.png"
            )

            image_editor.preprocess_image()
            ranking = visionapi.read_result_to_ranking()
            analyzer.assign_points(ranking)

            for user in ranking:
                print(user.get_dict())

            print("タグと名前を設定します...")
            tag_users = analyzer.set_tag_and_name(ranking, 2)
            
            for tag_user in tag_users:
                print(tag_user.get_dict())

            # ユーザーデータを累積
            with all_users_lock:
                for user in tag_users:
                    key = user.raw_name
                    if key in all_users:
                        # 既存のユーザーの場合、ポイントを累積
                        all_users[key].points.extend(user.points)
                    else:
                        # 新規ユーザーの場合、ユーザーを追加
                        all_users[key] = user

            total_points_by_tag = analyzer.calculate_total_points_by_tag(list(all_users.values()))
            total_points_by_tag.sort(key=lambda x: x['points'], reverse=True)
            
            with data_lock:
                data = total_points_by_tag

            print("合計ポイント:")
            for item in data:
                print(f"{item['tag']}: {item['points']}")

            time.sleep(10)
            # running = False

if __name__ == "__main__":
    # 画像処理スレッドを開始
    flag_detection_thread = threading.Thread(target=run)
    flag_detection_thread.daemon = True
    flag_detection_thread.start()

    # Flaskアプリを実行
    app.run()
