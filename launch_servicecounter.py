import argparse
import time
import datetime
import os
from ai_servicecounter.gui_counter import ChatGUI
from ai_servicecounter.broker import Broker
from ai_servicecounter.counter import Counter
from ai_servicecounter.observer import Observer
from ai_servicecounter.reviewer import Reviewer
import json
from ai_scientist.llm import create_client
from typing import Any, List

current_timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

def add_invalid_value_log_to_script(speaker_role: str, attribute_name: str, script_history: List[str]):
    script_history.append(f"system: {attribute_name} of {speaker_role} is invalid value.")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run AI service counter")
    parser.add_argument("--job_path", type=str, required=True, help="Path to the job description file")
    parser.add_argument("--task_path", type=str, required=True, help="Path to the task details file")
    parser.add_argument("--model", type=str, required=True, help="Model name")
    parser.add_argument("--result_path", type=str, required=True, help="Path to the result file")
    parser.add_argument("--script_history_dir", type=str, required=True, help="Path to the script history file")
    return parser.parse_args()


def main(job_description_path: str, task_details_path: str, model: str, result_path: str, script_history_dir: str):

    # GUI
    app = ChatGUI()
    task_number = None
    job_description = None
    with open(job_description_path, "r", encoding="utf-8") as f:
        job_description = json.load(f)
    with open(task_details_path, "r", encoding="utf-8"  ) as f:
        task_details = json.load(f)
    client, client_model = create_client(model)
    indicators = job_description["reviewer"]["indicators"]
    # actual chat history
    script_history = []
    msg_history = []
    all_task_number = [task["task_number"] for task in task_details["tasks"]]
    correct_img_path_format = "conf/correct_img/{task_number}.png"
    counter = Counter(job_description=job_description)
    observer = Observer(job_description=job_description, task_details=task_details)
    reviewer = Reviewer(job_description=job_description)
    broker = Broker(job_description=job_description, task_details=task_details)
    running = True
    step = 0
    while running:
        app.update_idletasks()
        app.update()

        # Avoid errors when GUI is closed (e.g., window X button)
        if not app.winfo_exists():
            break
        # If user input is available, send it to LLM
        if app.user_input_flag:
            user_message = app.user_message

            image_path = [] if app.user_image_path is None else [app.user_image_path]
            # analyze situation
            extracted_json, msg_history, script_history = counter.analyze_situation(text =user_message, client=client, model=model, image_paths=image_path, msg_history=msg_history, script_history=script_history)
            if extracted_json["need_help_collegue"] != "":
                if extracted_json["need_help_collegue"] == "broker":
                    extracted_json, msg_history, script_history = broker.identify_task(task_details=task_details, text =extracted_json, client=client, model=model, image_paths=image_path, msg_history=msg_history, script_history=script_history)
                    if extracted_json["task_number"].isdigit():
                        if int(extracted_json["task_number"]) in all_task_number:
                            task_number = extracted_json["task_number"]
                        else:
                            add_invalid_value_log_to_script(speaker_role="broker", attribute_name="task_number", script_history=script_history)

                elif extracted_json["need_help_collegue"] == "reviewer":
                    if task_number is not None:
                        correct_img_path = correct_img_path_format.format(task_number=task_number)
                        extracted_json, msg_history, script_history = reviewer.review_correctness_with_img( client=client, model=model, image_paths=image_path + [correct_img_path], msg_history=msg_history, script_history=script_history)
                    else:
                        correct_img_paths = [correct_img_path_format.format(task_number=task_number) for task_number in all_task_number]
                        task_list = [f"タスク{task_number}: {task_details['tasks'][task_number]['task_content']}" for task_number in all_task_number]
                        extracted_json, msg_history, script_history = reviewer.review_correctness_with_img(task_list=task_list, client=client, model=model, image_paths=image_path + correct_img_paths, msg_history=msg_history, script_history=script_history)

                        add_invalid_value_log_to_script(speaker_role="counter", attribute_name="task_number", script_history=script_history)
                else:
                    add_invalid_value_log_to_script(speaker_role="counter", attribute_name="need_help_collegue", script_history=script_history)

            # Counter's message to user
            extracted_json, msg_history, script_history = counter.respond_with_context(text =user_message, client=client, model=model, msg_history=msg_history, script_history=script_history)
            print(extracted_json)
            # Display response in GUI
            app.add_chat("Counter", extracted_json["response"])

            extracted_json, msg_history, script_history = observer.observe_to_continue_interaction(client=client, model=model, msg_history=msg_history, script_history=script_history)
            try:
                is_need_of_continuation_of_interaction = int(extracted_json["is_need_of_continuation_of_interaction"])
                if is_need_of_continuation_of_interaction == 0:
                    running = False

            except:
                add_invalid_value_log_to_script(speaker_role="observer", attribute_name="is_need_of_continuation_of_interaction", script_history=script_history)
            app.set_input_in_progress(False)

            print(f"step: {step}, msg_history: {msg_history}, script_history: {script_history}")
            step += 1
        # Avoid errors when GUI is closed (e.g., window X button)
        time.sleep(0.01)

    # End process
    if app.winfo_exists():
        app.destroy()

    # generate result indicator
    extracted_json, msg_history, script_history = reviewer.review_score(indicators=indicators,  client=client, model=model, image_paths=[image_path], msg_history=msg_history, script_history=script_history)
    extracted_json["timestamp"] = current_timestamp
    with open(result_path, "w") as f:
        json.dump(extracted_json, f)
    try:
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {result_path}")
        result_data = []

    result_data.append(extracted_json)

    # !TODO: Add exclusive control
    with open(result_data, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=4)

    with open(os.path.join(script_history_dir,current_timestamp, "_script_history.json")  , "w", encoding="utf-8") as f:
        json.dump(script_history, f, ensure_ascii=False, indent=4)



if __name__ == "__main__":
    args = parse_arguments()
    job_description_path = args.job_path
    task_details_path = args.task_path
    result_path = args.result_path
    script_history_dir = args.script_history_dir
    model = args.model
    main(script_history_dir=script_history_dir, job_description_path=job_description_path, task_details_path=task_details_path, model=model, result_path=result_path)
