def run(tool_input):
    message = tool_input["message"]
    if any(ch.isdigit() for ch in message):
        raise RuntimeError("Digits are not allowed in message")
    return {"text": message}
