from typing import Dict, List
from ai_scientist.llm import get_response_and_scripts_from_llm
from typing import Dict, List
from ai_servicecounter.worker import Worker
base_prompt = """
あなたは{job_description[workplace]}に勤務する{job_type}の監督者です。
会話履歴から、既に顧客の要件が満たされた、もしくはさらに会話を継続することで顧客の要件が満たされる可能性があるか判断してください。
判断された情報は、レスポンスフォーマットに従って出力してください。

# レスポンスフォーマット(JSON)
json
{
"is_need_of_continuation_of_interaction": 0 or 1,
"reason": [判断した理由],
"own_thought": [判断した理由を踏まえた自分の考え]
}

"""
class Observer(Worker):
    def __init__(self, base_prompt: str, job_description: Dict[str, str]):
        self.job_description = job_description
        self.speaker_role = "オブザーバー"
        self.base_prompt = base_prompt
    def observe_to_continue_interaction(self, model: str, client: str, msg_history:str =None, return_msg_history: bool =False, system_prompt: str =None, script_history: List[str] =None) -> Dict[str, str]:
        """
        Observes and analyzes the interaction between customer and service counter.

        Args:
            model: LLM model
            client: LLM client
            msg_history: Conversation history
            return_msg_history: Whether to return conversation history
            system_prompt: System prompt
            script_history: List of previous script outputs


        """
        str_task_details = "\n".join([f"{k}: {v}" for k, v in self.task_details.items()])



        resp, msg_histories, script_histories = get_response_and_scripts_from_llm(
            base_prompt=self.base_prompt.format(job_description=self.job_description),
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

