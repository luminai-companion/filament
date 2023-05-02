def trim_response(response_text: str, stop_tokens: list[str]) -> str:
    if not stop_tokens:
        return response_text

    first_match_ind = min(
        list(filter(lambda x: x >= 0, [response_text.find(x) for x in stop_tokens])),
        default=None,
    )

    if first_match_ind is None:
        return response_text

    response_text = response_text[0 : first_match_ind - 1]
    return response_text


def inject_into_prompt(prompt: str, lines: str) -> str:
    ind = prompt.find("<START>")

    if ind >= 0:
        prompt = prompt[:ind] + lines + prompt[ind:]

    return prompt
