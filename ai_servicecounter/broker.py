from typing import Dict, List
from ai_scientist.llm import get_response_and_scripts_from_llm
from typing import Dict, List
from ai_servicecounter.worker import Worker

base_prompt = """
あなたは{workplace}で{job_type}から伝えられる文脈情報から、
顧客の要望が業務リスト上に記載のあるどのタスクに該当し、どのステータスであるかを判断してください。
該当するタスクがない場合は、task_nameに"なし"と記載してください。
判断された情報は、レスポンスフォーマットに従って出力してください。
以下に、文脈情報およびそのフォーマット、業務リストとレスポンスフォーマットを記載します。

# 業務リスト
{str_task_details}

# レスポンスフォーマット(JSON)
json
{{
"task_name": [判断されたタスクのタイプ],
"requirements": [判断されたタスクの要件],
"status": [判断されたタスクのステータス],
"next_action": [判断されたタスクの次のアクション]
"own_thought": [判断した理由を踏まえた自分の考え]
}}

"""


class Broker(Worker):
    def __init__(self, job_description: Dict[str, str], task_details: Dict[str, str], base_prompt: str = base_prompt):
        self.job_description = job_description
        self.task_details = task_details
        self.speaker_role = "ブローカー"
        str_task_details = "\n".join([f"{k}: {v}" for k, v in self.task_details.items()])
        self.system_message = base_prompt.format(job_type=self.job_description["job_type"],  workplace=self.job_description["workplace"], str_task_details=str_task_details),
    def identify_task(self, str, text: str, model: str, client: str, msg_history:str =None, script_history: List[str] =None) -> Dict[str, str]:


        identify_prompt = """

        # 文脈情報
        {text}

        # 文脈情報のフォーマット
        {{
        "desire": [顧客の要望],
        "current_situation": [顧客の現在の状況]
        "language": [顧客の言語]
        }}
        """

        resp, msg_histories, script_history = get_response_and_scripts_from_llm(
            msg=identify_prompt.format(text=text),
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

