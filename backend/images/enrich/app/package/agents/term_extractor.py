from package.prompt.core import PromptGenerator
from package.prompt.interface import Persona, Instructions, Examples, Example
from package.agents.core import BroAgent
from pydantic import BaseModel, Field
from typing import List, Literal
from package.llm.ollama import BedrockOllamaChat

bedrock_model = BedrockOllamaChat(
    model_name="us.meta.llama3-3-70b-instruct-v1:0",
    temperature=0,
)

class InputContext(BaseModel):
    context: str = Field(description="The input text or passage to analyze.")

class ExtractedTerm(BaseModel):
    term: str = Field(description="The extracted term, such as a technical term, acronym, abbreviation, jargon, framework, or algorithm.")
    type: Literal["Acronym", "Abbreviation", "Framework", "Algorithm", "Technical Term", "Jargon", "Proper Name"] = Field(description="The type of the extracted term.")
    evidence: str = Field(description="The specific sentence or phrase from the text where the term appears.")
    explanation: str = Field(description="A short explanation based on the evidence. Avoid making assumptions.")

class ExtractedTerms(BaseModel):
    terms: List[ExtractedTerm] = Field(description="A list of extracted terms with type, evidence, and explanation.")

prompt_generator = PromptGenerator(
    persona=Persona(
        name="Jame",
        description="The best proofreader who can spot any jargon, acronym, abbreviation, proper name, framework, or algorithm with ease."
    ),
    instructions=Instructions(
        instructions=[
            "Extract any term that is a technical term, jargon, acronym, abbreviation, proper name, framework name, algorithm, scientific theory, biological system, or system component.",
            "For each term, provide its type (e.g., Acronym, Framework, Algorithm, etc).",
            "Also extract supporting evidence from the input context (where it appears).",
            "Write a short explanation **only based on the evidence** provided in the text.",
            "Always avoid extracting person names.",
            "Avoid hallucination: if the meaning is not clearly supported in the context, do not guess it.",
        ],
        cautions=[
            "Do not extract everything — extract only clear and certain terms with strong signals.",
            "Do not extract if there is no supporting evidence in the text.",
            "If unsure whether something qualifies, err on the side of skipping it.",
            "Always respond in the specified JSON schema with 'term', 'type', 'evidence', and 'explanation'."
        ]
    ),
    structured_output=ExtractedTerms,
    examples=Examples(examples=[
        Example(
            setting="Academic Journal",
            input=InputContext(context="Andrew Ng said, The new era of LLM, large language model, comes faster than anyone expected. It works well with RAG, retrieval augmented generation, and it allows agentic framework to ..."),
            output=ExtractedTerms(terms=[
                ExtractedTerm(
                    term="LLM",
                    type="Acronym",
                    evidence="The new era of LLM, large language model",
                    explanation="LLM stands for large language model"
                ),
                ExtractedTerm(
                    term="RAG",
                    type="Acronym",
                    evidence="It works well with RAG, retrieval augmented generation",
                    explanation="RAG stands for retrieval augmented generation"
                ),
                ExtractedTerm(
                    term="agentic framework",
                    type="Framework",
                    evidence="... and it allows agentic framework to ...",
                    explanation="Agentic framework refers to a system where agents operate with autonomy"
                )
            ])
        )
    ]),
    fallback=None
)

class TermExtractor:
    def __init__(self):
        self.agent = BroAgent(prompt_generator=prompt_generator, model=bedrock_model)

    def run(self, context: str) -> List[ExtractedTerm] | None:
        request = InputContext(context=context)
        response = self.agent.run(request)
        if response is not None and isinstance(response, ExtractedTerms):
            return response.terms
        return None
