from typing import Dict, List
from ai_scientist.llm import get_response_and_scripts_from_llm
from typing import Dict, List
from ai_servicecounter.worker import Worker

base_prompt = """
あなたは{job_description[workplace]}で{job_type}から伝えられる文脈情報から、
顧客の要望が業務リスト上に記載のあるどのタスクに該当し、どのステータスであるかを判断してください。
該当するタスクがない場合は、task_nameに"なし"と記載してください。
判断された情報は、レスポンスフォーマットに従って出力してください。
以下に、文脈情報およびそのフォーマット、業務リストとレスポンスフォーマットを記載します。

# 文脈情報
{text}

# 文脈情報のフォーマット
{
"desire": [顧客の要望],
"current_situation": [顧客の現在の状況]
"language": [顧客の言語]
}

# 業務リスト
{str_task_details}

# レスポンスフォーマット(JSON)
json
{
"task_name": [判断されたタスクのタイプ],
"requirements": [判断されたタスクの要件],
"status": [判断されたタスクのステータス],
"next_action": [判断されたタスクの次のアクション]
"own_thought": [判断した理由を踏まえた自分の考え]
}

"""


class Broker(Worker):
    def __init__(self, base_prompt: str, job_description: Dict[str, str], task_details: Dict[str, str]):
        self.job_description = job_description
        self.task_details = task_details
        self.speaker_role = "ブローカー"
        self.base_prompt = base_prompt
    def identify_task(self, job_type: str, text: str, model: str, client: str, msg_history:str =None, return_msg_history: bool =False, system_prompt: str =None, script_history: List[str] =None) -> Dict[str, str]:
        """Identifies the appropriate task based on customer response and conversation history.

        Args:
            job_type: Type of job
            text: Customer response
            model: LLM model
            client: LLM client
            msg_history: Conversation history
            return_msg_history: Whether to return conversation history
            system_prompt: System prompt
        Returns:
            Dict[str, str]: Dictionary containing identified task details including:
                - task_type: Type of task to be performed
                - priority: Priority level of the task
                - requirements: Any specific requirements for the task
                - status: Current status of task identification
        """
        str_task_details = "\n".join([f"{k}: {v}" for k, v in self.task_details.items()])


        resp, msg_histories, script_histories = get_response_and_scripts_from_llm(
            base_prompt=self.base_prompt.format(text=text,job_type=job_type, msg_history=msg_history, job_description=self.job_description, str_task_details=str_task_details),
            model=model,
            client=client,
            system_message=system_prompt,
            print_debug=False,
            msg_history=msg_history,
            return_msg_history=return_msg_history,
            temperature=0.75,
            speaker_role=self.speaker_role,
            script_history=script_history,
        )
        extracted_json = self._extract_json(resp)
        return extracted_json, msg_histories, script_histories

