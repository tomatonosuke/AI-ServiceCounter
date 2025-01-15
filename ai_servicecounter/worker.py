
from ai_scientist.llm import extract_json_between_markers


class Worker():
    """
    Base class for workers.
    """

    def _extract_json(self, resp):
        json_output = extract_json_between_markers(resp)
        assert json_output is not None, f"Error parsing json from {self.speaker_role}: {resp}"
        return json_output
