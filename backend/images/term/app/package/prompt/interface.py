from typing import List, Optional, Union
from pydantic import BaseModel, Field
from package.prompt.utils import get_input, get_return_json_schema

class Persona(BaseModel):
    name: str = Field(description="An agent's name.")
    description: str = Field(description="A short description describes an agent's characteristics.")

    def as_prompt(self):
        return f"Persona:\n\t- Name: {self.name}\n\t- Description: {self.description}"

class Instructions(BaseModel):
    instructions:List[str] = Field(description="The instructions (tasks) that the agent must do, make it as imperative sentence.")
    cautions:Optional[List[str]] = Field(description="Cautions is unlike tasks, but if you don't do this, something bad or error might happen.", default=None)

    def as_prompt(self):
        instructions_str = "Instructions:\n"+"\n".join([f"\t- {text}" for text in self.instructions])
        cautions = self.cautions
        if cautions is not None and isinstance(cautions, list):
            cautions_str = "\nCautions:\n"+"\n".join([f"\t- {text}" for text in cautions])
            return instructions_str+cautions_str
        return instructions_str
    
class Example(BaseModel):
    setting: str = Field(description="The setting of the example")
    input: Union[str, BaseModel] = Field(description="The input example based on InputFormat of each agent.")
    output: Union[str, BaseModel] = Field(description="The output example based on OutputFormat of each agent.")

class Examples(BaseModel):
    examples:List[Example] = Field(description="List of examples to be followed.")

    def _validate_input(self, obj):
        if isinstance(obj, str):
            return obj
        if isinstance(obj, BaseModel):
            return get_input(obj)
        raise TypeError(f"{type(obj)} is not implemented yet, try {type(str)} or {type(BaseModel)}")

    def _validate_output(self, obj):
        if isinstance(obj, str):
            return obj
        if isinstance(obj, BaseModel):
            return get_return_json_schema(obj)
        raise TypeError(f"{type(obj)} is not implemented yet, try {type(str)} or {type(BaseModel)}")
    
    def as_prompt(self):
        examples = []
        for enum, example in enumerate(self.examples):
            ex_input = self._validate_input(example.input)
            ex_output = self._validate_output(example.output)
            prompt = f"""Example {enum+1}: "{example.setting}"\n{ex_input}\n\n{ex_output}"""
            examples.append(prompt)
        return "\n\n".join(examples)


        