from package.prompt.core import PromptGenerator
from package.prompt.interface import Persona, Instructions, Examples, Example
from package.agents.core import BroAgent
from pydantic import BaseModel, Field
from typing import List
from package.llm.ollama import BedrockOllamaChat

# LLM setup
bedrock_model = BedrockOllamaChat(
    model_name="us.meta.llama3-2-11b-instruct-v1:0",
    temperature=0,
)

# Schema for detection
class InputMessage(BaseModel):
    message: str = Field(description="A user's input message")

class PotentialTerm(BaseModel):
    term: str = Field(description="A potential term, acronym, abbreviation, jargon, or proper name")
    confidence: float = Field(description="A score from 0 to 1 indicating confidence in this being a real term")

class PotentialTerms(BaseModel):
    terms: List[PotentialTerm] = Field(description="A list of potential terms with confidence scores")

# Prompt Generator
prompt_generator = PromptGenerator(
    persona=Persona(
        name="Smith",
        description="You are the best peer reviewer who knows all terms, acronyms, abbreviations, jargons, and proper names and can spot them easily."
    ),
    instructions=Instructions(
        instructions=[
            "Read the message carefully.",
            "Extract only obvious or certain terms, acronyms, abbreviations, jargon, or proper names.",
            "Assign a confidence score from 0 to 1 to each term. 1 means very confident, 0 means not confident.",
            "Avoid extracting person names."
        ],
        cautions=[
            "Not everything is a term — avoid over-extraction.",
            "If unsure about a term, do not include it.",
            "Always respond in the given JSON format."
        ]
    ),
    structured_output=PotentialTerms,
    examples=Examples(examples=[
        Example(
            setting="Academic Journal",
            input=InputMessage(message="Do you know what does LLM stand for?"),
            output=PotentialTerms(terms=[
                PotentialTerm(term="LLM", confidence=0.9)
            ])
        ),
        Example(
            setting="Blog Post",
            input=InputMessage(message="In the age of AI, LLM and RAG are the most implemented systems across all business sectors."),
            output=PotentialTerms(terms=[
                PotentialTerm(term="LLM", confidence=1.0),
                PotentialTerm(term="RAG", confidence=0.9)
            ])
        )
    ]),
    fallback=None,
)

# ✅ TermDetector for term matching
class TermDetector:
    def __init__(self, confidence_threshold: float = 0.5):
        self.agent = BroAgent(prompt_generator=prompt_generator, model=bedrock_model)
        self.confidence_threshold = confidence_threshold

    def run(self, message: str) -> List[str]:
        request = InputMessage(message=message)
        potential_terms = self.agent.run(request)
        if potential_terms and isinstance(potential_terms, PotentialTerms):
            filtered = [t.term for t in potential_terms.terms if t.confidence > self.confidence_threshold]
            return filtered
        return []
