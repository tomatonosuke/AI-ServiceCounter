from typing import Dict, List
from ai_scientist.llm import get_response_and_scripts_from_llm
from typing import Dict, List
from ai_servicecounter.worker import Worker
base_prompt = """
あなたは{workplace}に勤務する{job_type}の監督者です。

"""
class Observer(Worker):
    def __init__(self, job_description: Dict[str, str],task_details: Dict[str, str], base_prompt: str = base_prompt):
        self.job_description = job_description
        self.task_details = task_details
        self.speaker_role = "observer"

        self.system_message = base_prompt.format(workplace=self.job_description["workplace"],job_type=self.job_description["job_type"])

    def observe_to_continue_interaction(self, model: str, client: str, msg_history:str =None, script_history: List[str] =None) -> Dict[str, str]:
        str_script_history = '\n'.join(script_history)
        str_task_details = "\n".join([f"{k}: {v}" for k, v in self.task_details.items()])
        observe_prompt = """
        会話履歴から、既に顧客の要件が満たされた、もしくはさらに会話を継続することで顧客の要件が満たされる可能性があるか判断してください。
        判断された情報は、レスポンスフォーマットに従って出力してください。

        # タスク詳細
        {str_task_details}

        # 会話履歴
        {str_script_history}

        # レスポンスフォーマット(JSON)
        json
        {{
        "is_need_of_continuation_of_interaction": 0 or 1 (0:会話継続が不要, 1:会話継続が必要),
        "reason": 判断した理由,
        "own_thought": 判断した理由を踏まえた自分の考え
        }}

        """
        resp, msg_histories, script_history = get_response_and_scripts_from_llm(
            msg=observe_prompt.format(str_script_history=str_script_history, str_task_details=str_task_details),
            system_message=self.system_message,
            model=model,
            client=client,
            print_debug=False,
            msg_history=msg_history,
            temperature=0.75,
            speaker_role=self.speaker_role,
            script_history=script_history,
        )
        extracted_json = self._extract_json(resp)
        return extracted_json, msg_histories, script_history
