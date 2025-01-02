import os
import json
import requests
from ai_scientist.llm import get_response_and_scripts_from_llm, get_response_and_scripts_with_img_from_llm
from ai_servicecounter.worker import Worker
from typing import Dict, List

base_prompt = """
あなたは{workplace}で{job_type}の窓口対応をしています。
以下に同僚名と同僚が実施できるタスクを記載します。
{collegues}
礼儀正しい対応を心がけてください。
以下に、これまでの会話履歴と、顧客からのメッセージを記載します。

# 会話履歴
{msg_history}

# 顧客からのメッセージ
{text}

"""


class Counter(Worker):
    def __init__(self, base_prompt: str, job_description: Dict[str, str], max_attempts: int = 10):
        self.max_attempts = max_attempts
        self.current_attempt = 0
        self.job_description = job_description
        self.speaker_role = "counter"
        self.base_prompt = base_prompt

    def analyze_situation(self, image_paths: List[str], text: str, model: str, client: str, msg_history:str =None, return_msg_history: bool =False, system_prompt: str =None, script_history: List[str] =None):


        check_situation_prompt = self.base_prompt + """
        会話履歴と顧客からのメッセージをもとに、以下のフォーマットにて記載された情報を出力してください。
        また、後続タスクを頼む同僚の名前をneed_help_collegueに出力してください。不要な場合は空文字列にしてください。
        # レスポンスフォーマット(JSON)
        json
        {
        "desire": [顧客の要望],
        "current_situation": [顧客の現在の状況],
        "language": [顧客の言語],
        "own_thought": [顧客の要望を踏まえた自分の考え],
        "need_help_collegue": [後続タスクを実施する同僚名]

        }
        """

        resp, msg_histories, script_histories = get_response_and_scripts_with_img_from_llm(
            base_prompt= check_situation_prompt.format(text=text, msg_history=msg_history, collegues=self.job_description["counter"]["collegues"],workplace=self.job_description["workplace"],job_type=self.job_description["job_type"]),
            image_paths=image_paths,
            model=model,
            client=client,
            system_message=system_prompt,
            print_debug=False,
            msg_history=msg_history,
            return_msg_history=return_msg_history,
            # Higher temperature to encourage diversity.
            temperature=0.75,
            speaker_role=self.speaker_role,
            script_history=script_history,
        )
        extracted_json = self._extract_json(resp)
        return extracted_json, msg_histories, script_histories

    def respond_with_context(self, text: str, model: str, client: str, msg_history:str =None, return_msg_history: bool =False, system_prompt: str =None, script_history: List[str] =None):

        get_response_prompt = self.base_prompt + """
        会話履歴と顧客からのメッセージをもとに、以下のフォーマットにて記載された情報を出力してください。
        顧客の言語に合わせて回答してください。

        # レスポンスフォーマット(JSON)
        json
        {
        "response": [会話履歴を踏まえた顧客への回答],
        "language": [顧客の言語],
        "own_thought": [顧客の要望を踏まえた自分の考え]
        }
        """
        try:
            resp, msg_histories, script_histories = get_response_and_scripts_with_img_from_llm(
                base_prompt= get_response_prompt.format(text=text, msg_history=msg_history, job_description=self.job_description),
                model=model,
                client=client,
                system_message=system_prompt,
                print_debug=False,
                msg_history=msg_history,
                return_msg_history=return_msg_history,
                # Higher temperature to encourage diversity.
                temperature=0.75,
                speaker_role=self.speaker_role,
                script_history=script_history,
            )
            extracted_json = self._extract_json(resp)

            return extracted_json, msg_histories, script_histories
        except Exception as e:
            print(f"Error: {e}")
            return None, None, None
