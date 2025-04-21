# helper methods

from fastapi.responses import JSONResponse
import re


def extract_session_id(output_context_name):
    """Extract the session ID from a DialogFlow response"""
    session_id_pattern = r"sessions/([0-9a-f-]+)/contexts/"

    try:
        if output_context_name:
            context_name = output_context_name.get("name", "")
            match = re.search(session_id_pattern, context_name)
            if match:
                return match.group(1)
    except (AttributeError, IndexError):
        pass
    return None
