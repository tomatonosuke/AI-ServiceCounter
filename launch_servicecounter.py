import argparse
import time
from ai_servicecounter.gui_counter import ChatGUI
from ai_servicecounter.broker import Broker
from ai_servicecounter.counter import Counter
from ai_servicecounter.observer import Observer
from ai_servicecounter.reviewer import Reviewer
import json
from ai_scientist.llm import create_client

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run AI service counter")
    parser.add_argument("--job_path", type=str, required=True, help="Path to the job description file")
    parser.add_argument("--task_path", type=str, required=True, help="Path to the task details file")
    parser.add_argument("--model", type=str, required=True, help="Model name")
    parser.add_argument("--gpus", type=int, required=True, help="Number of GPUs")
    return parser.parse_args()

def main(job_description_path: str, task_details_path: str, model: str, gpus: int, client: Any):

    # GUI
    app = ChatGUI()
    task_number = None
    job_description = None
    with open(task_details_path, "r") as f:
        job_description = json.load(f)
    with open(task_details_path, "r") as f:
        task_details = f.read()
    client, client_model = create_client(model)

    # actual chat history
    script_history = []
    msg_history = []

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
            extracted_json, msg_histories, script_histories = counter.analyze_situation(text =user_message, client=client, model=model, image_paths=[image_path], msg_history=msg_histories, script_history=script_histories)
            if extracted_json["need_help_collegue"] != "":
                if extracted_json["need_help_collegue"] == "broker":
                    extracted_json, msg_histories, script_histories = broker.identify_task(task_details=task_details, text =user_message, client=client, model=model, image_paths=[image_path], msg_history=msg_histories, script_history=script_histories)
                    if extracted_json["task_number"].isdigit():
                        task_number = extracted_json["task_number"]
                elif extracted_json["need_help_collegue"] == "reviewer":
                    extracted_json, msg_histories, script_histories = reviewer.review_correctness_with_img(text =user_message, client=client, model=model, image_paths=[image_path], msg_history=msg_histories, script_history=script_histories)

            extracted_json, msg_histories, script_histories = counter.respond_with_context(text =user_message, client=client, model=model, msg_history=msg_histories, script_history=script_histories)
            # GUIに応答を表示
            app.add_chat("LLM", extracted_json["response"])

            if "終了" in response:
                running = False

        # ループが速すぎる場合に少し待機 (CPU 負荷軽減)
        time.sleep(0.01)

    # 終了処理
    if app.winfo_exists():
        app.destroy()
    extracted_json, msg_histories, script_histories = reviewer.review_score(text =user_message, client=client, model=model, image_paths=[image_path], msg_history=msg_histories, script_history=script_histories)

if __name__ == "__main__":
    args = parse_arguments()
    job_description_path = args.job_path
    task_details_path = args.task_path
    model = args.model
    gpus = args.gpus
    main(job_description_path=job_description_path, task_details_path=task_details_path, model=model, gpus=gpus)
