from typing import Any, Callable, List, Union
from pydantic import BaseModel
from package.prompt.core import PromptGenerator
from package.prompt.core import Persona, Instructions
from package.prompt.utils import get_input, parse_json_output
# from broai.experiments.utils import experiment

from abc import ABC, abstractmethod
from typing import Any

class LLMChatInterface(ABC):

    @abstractmethod
    def UserMessage(self, text:str) -> Any:
        pass

    @abstractmethod
    def AIMessage(self, text:str) -> Any:
        pass

    @abstractmethod
    def SystemMessage(self, text:str) -> Any:
        pass

    @abstractmethod
    def run(self, formatted_prompt: Any) -> str:
        pass

class BroAgent:
    def __init__(
            self,
            prompt_generator:PromptGenerator,
            model:LLMChatInterface,
            retry:int=1,
            tools:List[Callable] = None
    ):
        self.prompt_generator = prompt_generator
        self.model = model
        self.retry = retry
        self.tools = tools
        self.cnt = 0
        self.__errors = []

    def get_error_msg(self, errors:List[str])->str:
        if len(errors)==0:
            return ""
        return "Avoid the following errors: \n\n{error_msg}".format(error_msg="\n".join(errors))

    def parse_structured_output(self, text:str):
        parsed_json = parse_json_output(text)
        structured_output = self.prompt_generator.structured_output.model_validate_json(parsed_json)
        return structured_output
    
    # @experiment
    def content_extractor(self, text:str):
        pg = PromptGenerator(
            persona=Persona(name="BroAI", description="You are a content extractor."),
            instructions=Instructions(
                instructions=[
                    "Extract the content into the sepcified JSON format.",
                ],
            ),
            structured_output=self.prompt_generator.structured_output,
            fallback=self.prompt_generator.fallback
        )
        response = self.model.run(
            system_prompt=pg.as_prompt(),
            messages=[self.model.UserMessage(text=f"Content:\n\n{text}\n\n")]
        )
        return self.parse_structured_output(self, text=response)
    
    def response_pydantic(self, text: str):
        try:
            return self.parse_structured_output(text=text)
        except Exception as e1:
            try:
                return self.content_extractor(text)
            except Exception as e2:
                print(f"\033[91mBoth parse_structured_output and content_extractor failed:\n{e1}\n{e2}\033[0m")
                return None

    def _run(self, request):
        response = self.model.run(
            system_prompt=self.prompt_generator.as_prompt(), 
            messages=[self.model.UserMessage(request + "\n" + self.get_error_msg(self.__errors))]
        )
        if isinstance(self.prompt_generator.structured_output, str) or self.prompt_generator.structured_output is None:
            return response
        return self.response_pydantic(response)

    def read_errors(self):
        return self.__errors
    
    def run(self, request:Union[str, BaseModel])->Any:
        self.cnt=0
        if isinstance(request, BaseModel):
            request = get_input(request)
        while self.cnt < self.retry:
            response = self._run(request)
            if response is not None:
                self.cnt = 0
                return response
            self.cnt += 1
        if response is None:
            # fallback is None -> default message
            if self.prompt_generator.fallback is None:
                return "unknown error"
            # in other case return as it is
            return self.prompt_generator.fallback