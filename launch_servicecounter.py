import time
from ai_servicecounter.gui_counter import ChatGUI
from ai_servicecounter.broker import Broker
from ai_servicecounter.counter import Counter
from ai_servicecounter.observer import Observer
from ai_servicecounter.reviewer import Reviewer
import json

def main():

    # GUI
    app = ChatGUI()
    task_type = None
    task_status = None
    next_action = None
    job_description = None
    with open(task_details_path, "r") as f:
        job_description = json.load(f)
    with open(task_details_path, "r") as f:
        task_details = json.load(f)
    counter = Counter(job_description=job_description, task_details=task_details)
    observer = Observer(job_description=job_description, task_details=task_details)
    reviewer = Reviewer(job_description=job_description, task_details=task_details)
    broker = Broker(counter=counter, observer=observer, reviewer=reviewer)
    # メインルーチン側でループを制御
    running = True
    while running:
        # まずは Tkinter のイベントを処理
        app.update_idletasks()
        app.update()

        # GUI が閉じられた (ウィンドウ×ボタン) 場合などでエラー回避
        if not app.winfo_exists():
            break
        counter = Counter()
        # ユーザーの入力があれば取り出して LLM へ投げる
        user_input = app.get_user_input()
        if user_input is not None:
            user_message, image_path = user_input
            # LLMで処理



            # GUIに応答を表示
            app.add_chat("LLM", response)

            # ▼ ここで応答を見て終了条件を判定 ▼
            # 例えば LLM の返答が「終了」と含まれていたらメインループを抜ける
            if "終了" in response:
                running = False

        # ループが速すぎる場合に少し待機 (CPU 負荷軽減)
        time.sleep(0.01)

    # 終了処理
    if app.winfo_exists():
        app.destroy()

if __name__ == "__main__":
    args = parse_arguments()
    job_description_path = args.job_path
    task_details_path = args.task_path
    main()
