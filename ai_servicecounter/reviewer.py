from ai_servicecounter.worker import Worker
from typing import Dict, List


base_prompt = """

"""

class Reviewer(Worker):
    def __init__(self, job_description: Dict[str, str]):
        self.job_description = job_description

    def review(self, model: str, client: str, msg_history:str =None, return_msg_history: bool =False, system_prompt: str =None, script_history: List[str] =None) -> Dict[str, str]:
