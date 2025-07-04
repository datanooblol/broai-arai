from package.prompt.core import PromptGenerator
from package.prompt.interface import Persona, Instructions, Examples, Example
from package.agents.core import BroAgent
from pydantic import BaseModel, Field
from typing import List
# you can use any model sharing the same methods: .run, .SystemMessage, .UserMessage, .AIMessage
from package.llm.ollama import BedrockOllamaChat

bedrock_model = BedrockOllamaChat(
    model_name="us.meta.llama3-2-3b-instruct-v1:0",
    temperature=0,
)

class InputMessage(BaseModel):
    message:str = Field(description="a user's input message")

class PotentialJargon(BaseModel):
    jargon:str = Field(description="a potential jargon, acronym, abbreviation, or proper name")
    confidence:float = Field(description="a score ranging from 0 to 1. 0 means you're not confident whereas 1 is you're really confident")

class PotentialJargons(BaseModel):
    jargons:List[PotentialJargon] = Field(description="a list of potential jargon")

prompt_generator = PromptGenerator(
    persona=Persona(name="Smith", description="You are the best peer reviewer who knows all jargons, acronyms, abbreviations and proper names and you can spot them all easily."),
    instructions=Instructions(
        instructions=[
            "read content carefully",
            "extract only jargon, acronym, abbrevation, or proper name",
            "in each extraction, give a confidence score ranging from 0 to 1. 0 means you're not confident whereas 1 is you're really confident"
            "always avoid extracting the person name",
        ],
        cautions=[
            "Remember not everything is jargon, acronym, abbrevation or proper name, so do not try to extract everything, try only obvious or certain."
            "if you are not sure if it's a jargon, acronym, abbreviation, proper name, do not extract it",
            "respond in specified JSON format as in examples"
        ]
    ),
    structured_output=PotentialJargons,
    examples=Examples(examples=[
        Example(
            setting="Academic Journal",
            input=InputMessage(message="Do you know what does LLM stand for?"),
            output=PotentialJargons(jargons=[
                PotentialJargon(
                    jargon="LLM",
                    confidence=.9
                )
            ])
        ),
        Example(
            setting="Blog Post",
            input=InputMessage(message="In the age of AI, LLM and RAG are the most implemented systems across all business sectors."),
            output=PotentialJargons(jargons=[
                PotentialJargon(
                    jargon="LLM",
                    confidence=1
                ),
                PotentialJargon(
                    jargon="RAG",
                    confidence=.9
                ),
            ])
        ),
    ]),
    # fallback=PotentialJargons(jargons=[PotentialJargon(jargon="error", confidence=0)]),
    fallback=None,
)

class JargonDetector:
    def __init__(self, confidence:float=.5):
        self.agent = BroAgent(prompt_generator=prompt_generator,model=bedrock_model)
        self.confidence = confidence

    def run(self, message:str):
        request = InputMessage(message=message)
        potential_jargons = self.agent.run(request)
        detected_jargons = [j for j in potential_jargons.jargons if j.confidence>self.confidence]
        detected_jargons = [j.jargon for j in detected_jargons]
        return detected_jargons