from package.prompt.core import PromptGenerator
from package.prompt.interface import Persona, Instructions, Examples, Example
from package.agents.core import BroAgent
from pydantic import BaseModel, Field
from typing import List
# you can use any model sharing the same methods: .run, .SystemMessage, .UserMessage, .AIMessage
from package.llm.ollama import BedrockOllamaChat

bedrock_model = BedrockOllamaChat(
    model_name="us.meta.llama3-3-70b-instruct-v1:0",
    temperature=0,
)

class InputContext(BaseModel):
    context:str = Field(description="the input context.")

class Jargon(BaseModel):
    jargon:str = Field(description="the extracted jargon, acronym, abbreviation, proper name from the context"),
    evidence:str = Field(description="the evidence of the extracted jargon, acronym, abbreviation, proper name from the context"),
    explanation:str = Field(description="A short explanation based on the evidence.")

class Jargons(BaseModel):
    jargons:List[Jargon] = Field(description="A list of extracted jargons")

prompt_generator = PromptGenerator(
    persona=Persona(name="Jame", description="The best proof reader who can spot any jargon, acronym, abbreviation and proper name at ease."),
    instructions=Instructions(
        instructions=[
            "extract jargon, acronym, abbrevation, proper name and its evidence.",
            "also extract framework names, algorithms, scientific theories, biological systems, and any components used in the method",
            "create a short explanation of the extracted jargon, acronym, abbrevation, perper name based on its evidence.",
            "always avoid extracting the person name",
            "do not make up your explanation",
        ],
        cautions=[
            "Remember not everything is jargon, acronym, abbrevation or proper name, so do not try to extract everything, try only obvious or certain."
            "Do not extract jargon, acronym, abbreviation or proper name that does not contain evidence",
            "if you are not sure if it's a jargon, acronym, abbreviation, proper name, do not extract it",
            "respond in specified JSON format as in examples"
        ]
    ),
    structured_output=Jargons,
    examples=Examples(examples=[
        Example(
            setting="Academic Journal",
            input=InputContext(context="Andrew Ng said, The new era of LLM, large language model, comes faster than anyone expected. It works well with RAG, retrieveal augmented generation, and it allows agentic framework to ..."),
            output=Jargons(jargons=[
                Jargon(
                    jargon="LLM",
                    evidence="The new era of LLM, large language model",
                    explanation="LLM is a large language model"
                ),
                Jargon(
                    jargon="RAG",
                    evidence="It works well with RAG, retrieval augmented generation",
                    explanation="RAG is short for retrieval augmented generation"
                )
            ])
        )
    ]),
    # fallback=Jargons(jargons=[Jargon(jargon="error", evidence="error", explanation="error")]),
    fallback=None
)

class JargonExtractor:
    def __init__(self):
        self.agent = BroAgent(prompt_generator=prompt_generator, model=bedrock_model)

    def run(self, context:str) -> List[Jargon] | None:
        request = InputContext(context=context)
        response = self.agent.run(request)
        if response is not None and isinstance(response, Jargons):
            return response.jargons
        return None
        