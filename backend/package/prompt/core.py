from typing import Any, Union
from pydantic import BaseModel, field_validator
from package.prompt.utils import get_json_schema
from package.prompt.interface import Persona, Instructions, Examples

class PromptGenerator(BaseModel):
        persona:Union[str, Persona] = None
        instructions:Union[str, Instructions] = None
        structured_output:Any = None
        examples:Union[str, Examples] = None
        fallback:Any = None

        @field_validator("structured_output")
        @classmethod
        def validate_structured_output(cls, v):
            if isinstance(v, str):
                return v
            try:
                issubclass(v, BaseModel)
                return v
            except Exception as e:
                raise TypeError(f"structured_output must be: str, BaseModel")
    
        def get_prompt(self, obj, interface):
            # if the input is of type: str, None
            if (obj is None) or isinstance(obj, str):
                return obj
            # if the input is of types: Persona, Instructions, Examples
            if isinstance(obj, interface):
                return obj.as_prompt()
            # if the input isn't of type: BaseModel
            if not isinstance(obj, interface):
                return get_json_schema(obj)
            raise TypeError(f"{type(obj)} is invalid type, try None, {str}, {BaseModel} instead")
    
        def as_prompt(self):
            persona = self.get_prompt(self.persona, Persona)
            instructions = self.get_prompt(self.instructions, Instructions)
            structured_output = self.get_prompt(self.structured_output, BaseModel)
            examples = self.get_prompt(self.examples, Examples)
            prompt = []
            for p in [persona, instructions, structured_output, examples]:
                if p:
                    prompt.append(p)
            return "\n\n".join(prompt)