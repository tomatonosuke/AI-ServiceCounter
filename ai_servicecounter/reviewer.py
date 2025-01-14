from ai_servicecounter.worker import Worker
from typing import Dict, List
from ai_scientist.llm import encode_image, get_response_and_scripts_with_img_from_llm, get_response_and_scripts_from_llm
import datetime

base_prompt = """
あなたは{workplace}で{job_type}の評価者をしています。
今日は{current}です。和暦は令和7年です。

"""


class Reviewer(Worker):
    def __init__(self, job_description: Dict[str, str], base_prompt: str = base_prompt):
        self.job_description = job_description
        self.system_message = base_prompt.format(
            workplace=self.job_description["workplace"], job_type=self.job_description["job_type"], current=datetime.datetime.now())
        self.speaker_role = "reviewer"

    def review_correctness_with_img(self, correct_img_path: str, review_img_base64: str, model: str, client: str, msg_history: str = None, script_history: List[str] = None, task_list: List[str] = None) -> Dict[str, str]:
        review_correctness_prompt = """
        今から画像を２つ提出します。
        最初の画像が正解データで、2つ目の画像が提出されたデータです。
        2つの画像データを比較し、提出されたデータの正確性を判断してください。
        次のレスポンスは、以下レスポンスフォーマットに従って出力してください。
        今の会話はレスポンス不要です。

        # レスポンスフォーマット(JSON)
        ```json
        {{
        "is_approved": 0 or 1 (0:否認, 1:承認),
        "reason": 判断した理由,
        "need_correction": 修正すべき箇所,
        "correctness_score": 0-100
        }}
        ```
        """
        resp, msg_histories, script_histories = get_response_and_scripts_with_img_from_llm(
            msg=review_correctness_prompt,
            image_paths=[],
            image_base64_values=[correct_img_path],
            model=model,
            client=client,
            system_message=self.system_message,
            print_debug=False,
            msg_history=msg_history,
            temperature=0.75,
            speaker_role=self.speaker_role,
            script_history=script_history,
        )
        second_message = """
        2つめの画像を提出します。

        # レスポンスフォーマット(JSON)
        ```json
        {{
        "is_approved": 0 or 1 (0:否認, 1:承認),
        "reason": 判断した理由,
        "need_correction": 修正すべき箇所,
        "correctness_score": 0-100
        }}
        ```
        """
        resp, msg_histories, script_histories = get_response_and_scripts_with_img_from_llm(
            msg=second_message,
            image_paths=[],
            image_base64_values=[encode_image(review_img_base64)],
            model=model,
            client=client,
            system_message=self.system_message,
            print_debug=False,
            msg_history=msg_history,
            temperature=0.75,
            speaker_role=self.speaker_role,
            script_history=script_history,
        )

        return resp, msg_histories, script_histories

    def review_score(self, indicators: Dict[str, str], model: str, client: str, msg_history: str = None, script_history: List[str] = None) -> Dict[str, str]:
        indicator_str = "\n".join(
            [indicator["name"] + ": " + indicator["definition"] for indicator in indicators])
        str_script_history = '\n'.join(script_history)
        review_score_prompt = """
        {job_type}におけるやり取りを、評価指標欄に記載された指標に従って評価してください。
        以下のフォーマットに従って、以下の会話履歴の判断を評価してください。

        # 会話履歴
        {str_script_history}

        # 評価指標
        {indicator_str}

        # レスポンスフォーマット(JSON)
        ```json
        {{
        "indicator_name":
            {{
            "score": depend on the definition,
            "reason": 判断した理由,
            "need_correction": 修正すべき箇所
            }},
            ...
            ,
            "total_score": depend on the definition,
            "total_reason": 判断した理由を踏まえた自分の考え
        }}
        ```
        """
        resp, msg_histories, script_histories = get_response_and_scripts_from_llm(
            msg=review_score_prompt.format(
                job_type=self.job_description["job_type"], str_script_history=str_script_history, workplace=self.job_description["workplace"], indicator_str=indicator_str),
            model=model,
            client=client,
            system_message=self.system_message,
            print_debug=False,
            msg_history=msg_history,
            temperature=0.75,
            speaker_role=self.speaker_role,
            script_history=script_history,
        )
        extracted_json = self._extract_json(resp)
        return extracted_json, msg_histories, script_histories
