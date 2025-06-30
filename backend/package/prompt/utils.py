from pydantic import BaseModel
import json

def get_input(pydantic_obj:BaseModel):
    prompt = []
    for field_name, content in pydantic_obj.model_dump().items():
        prompt.append(f"{field_name.capitalize()}: \n{content}")
    return "".join(prompt)

_get_json_schema_prompt="""\
IMPORTANT:
	- Output only in a specified JSON format.
	- Do not include any premable, postmable, introductory, conversation, explanation or additional information.

Understand the following JSON schema and output only in a specified JSON format as in examples: 
""".strip()

def get_json_schema(pydantic_obj:BaseModel, json_instructions: str = _get_json_schema_prompt):
    prompt = f"""{json_instructions}\n{json.dumps(pydantic_obj.model_json_schema(), indent=4)}"""
    return prompt

def get_return_json_schema(object:BaseModel):
    prompt = f"""Output:\n```json\n{json.dumps(object.model_dump(), indent=4)}\n```"""
    return prompt

def parse_json_output(text:str):
    text = text.split("```")
    if len(text) == 1:
        text = text[0]
    else:
        text = "".join(text[1:])
    if text.startswith("json"):
        text = text[4:]

    text = text.split("```")
    if len(text) == 1:
        text = text[0]
    else:
        text = text[1]
    return text