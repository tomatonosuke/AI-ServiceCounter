
from ai_scientist.llm import extract_json_between_markers
class Worker:
    def __init__():
        pass
    def _extract_json(self, resp):
        json_output = extract_json_between_markers(resp)
        assert json_output is not None, "Failed to extract JSON from LLM output"
        return json_output
