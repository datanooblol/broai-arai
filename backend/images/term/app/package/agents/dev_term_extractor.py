from package.prompt.core import PromptGenerator
from package.prompt.interface import Persona, Instructions, Examples, Example
from package.agents.core import BroAgent
from pydantic import BaseModel, Field
from typing import List, Literal
from package.llm.ollama import BedrockOllamaChat

# Use the same LLM
bedrock_model = BedrockOllamaChat(
    model_name="us.meta.llama3-3-70b-instruct-v1:0",
    temperature=0,
)

# Schemas
class InputContext(BaseModel):
    context: str = Field(description="The input text or passage to analyze.")

class ExtractedTerm(BaseModel):
    term: str = Field(description="The extracted term, such as a technical term, acronym, abbreviation, jargon, framework, or algorithm.")
    type: Literal["Acronym", "Abbreviation", "Framework", "Algorithm", "Technical Term", "Jargon", "Proper Name"] = Field(description="The type of the extracted term.")
    evidence: str = Field(description="The full sentence or main clause from the context where the term appears.")
    explanation: str = Field(description="A short explanation based strictly on the evidence. Avoid assumptions.")

class ExtractedTerms(BaseModel):
    terms: List[ExtractedTerm] = Field(description="A list of extracted terms with type, evidence, and explanation.")

# Updated PromptGenerator
prompt_generator = PromptGenerator(
    persona=Persona(
        name="Jame",
        description="The best proofreader who can spot any jargon, acronym, abbreviation, proper name, framework, or algorithm with ease."
    ),
    instructions=Instructions(
        instructions=[
            "Extract any term that is a technical term, jargon, acronym, abbreviation, proper name, framework name, algorithm, scientific theory, biological system, or system component.",
            "For each term, provide its type (e.g., Acronym, Framework, Algorithm, etc).",
            "Extract the **entire sentence** (or clause) from the context where the term is used and use that as the evidence.",
            "Use complete sentences or full clauses as evidence. Avoid partial phrases unless it's clearly standalone.",
            "Write a short explanation strictly based on the extracted evidence. Do not make guesses.",
            "Avoid extracting person names."
        ],
        cautions=[
            "Do not extract everything — only include clear and certain terms with strong signals.",
            "Do not include any terms if the meaning or existence isn't clearly supported.",
            "Do not clip the sentence just to match the term — extract the full surrounding sentence or clause as evidence.",
            "Respond in the exact JSON format defined."
        ]
    ),
    structured_output=ExtractedTerms,
    examples=Examples(examples=[
        Example(
            setting="Academic Journal",
            input=InputContext(context=(
                "Andrew Ng said, The new era of LLM, large language model, comes faster than anyone expected. "
                "It works well with RAG, retrieval augmented generation, and it allows agentic framework to learn from feedback autonomously."
            )),
            output=ExtractedTerms(terms=[
                ExtractedTerm(
                    term="LLM",
                    type="Acronym",
                    evidence="The new era of LLM, large language model, comes faster than anyone expected.",
                    explanation="LLM stands for large language model and is presented as a transformative shift."
                ),
                ExtractedTerm(
                    term="RAG",
                    type="Acronym",
                    evidence="It works well with RAG, retrieval augmented generation, and it allows agentic framework to learn from feedback autonomously.",
                    explanation="RAG stands for retrieval augmented generation and is mentioned as compatible with LLMs."
                ),
                ExtractedTerm(
                    term="agentic framework",
                    type="Framework",
                    evidence="It works well with RAG, retrieval augmented generation, and it allows agentic framework to learn from feedback autonomously.",
                    explanation="Agentic framework is a system that learns from feedback, indicating autonomous operation."
                )
            ])
        )
    ]),
    fallback=None
)

# Final TermExtractor class
class TermExtractor:
    def __init__(self):
        self.agent = BroAgent(prompt_generator=prompt_generator, model=bedrock_model)

    def run(self, context: str) -> List[ExtractedTerm] | None:
        request = InputContext(context=context)
        response = self.agent.run(request)
        if response is not None and isinstance(response, ExtractedTerms):
            return response.terms
        return None
