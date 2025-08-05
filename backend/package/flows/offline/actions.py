from broflow import Action
from dataclasses import dataclass, field
from typing import List, Optional, Any
import asyncio
from brollm import BaseLLM
from package.databases.session import Depends, get_session
from package.databases.management.longterm import LongTermManagement, LongTerm
from package.databases.management.term import TermManagement, Term
from package.databases.management.term import TermManagement, Term
from package.embedding.baai import BAAIEmbedding
from broprompt import parse_codeblock_to_dict
from pydantic import BaseModel
from typing import List, Literal

def read_system_prompt(path:str):
    with open(path, 'r') as f:
        system_prompt = f.read()
    return system_prompt

@dataclass
class Shared:
    enrich_system_prompt:str
    term_system_prompt:str
    term_model:str
    # LongTerm contains both id, raw, meta and document_id
    chunk:LongTerm


class _Term(BaseModel):
    term: str
    type: Literal["Acronym", "Abbreviation", "Framework", "Algorithm", "Technical Term", "Jargon", "Proper Name"]
    evidence: str
    explanation: str

class Terms(BaseModel):
    terms: List[_Term]

class Embed(Action):
    """Embed all vectors at once and store in longterm"""
    def __init__(self, embedder:BAAIEmbedding):
        super().__init__()
        self.embedder = embedder

    def run(self, shared:Shared):
        return shared

class Enrich(Action):
    """Enrich with parallel calling and store in longterm"""
    def __init__(self, model:BaseLLM, db:LongTermManagement):
        super().__init__()
        self.model = model
        self.db = db

    def run(self, shared:Shared):
        system_prompt = read_system_prompt(shared.enrich_system_prompt)
        prompt = "##CONTEXT: \n\n{raw}\n\n##SUMMARY: \n\n".format(raw=shared.chunk.raw)
        summary = self.model.run(
            system_prompt=system_prompt,
            messages=[self.model.UserMessage(text=prompt)]
        )
        shared.chunk.enrich = summary
        shared.chunk.combo = f"{summary}\n\n{shared.chunk.raw}"
        self.db.update_longterms(longterms=[shared.chunk], session=Depends(get_session))
        return shared
    
class Jargon(Action):
    """Jargon with parallel calling and store in term"""
    def __init__(self, model:BaseLLM, db:TermManagement):
        super().__init__()
        self.model = model
        self.db = db

    def fallback(self, system_prompt, shared:Shared):
        errors = []
        for i in range(5):
            try:
                error = "Avoid below errors:\n\n{e}".format(e="\n".join(errors)) if len(errors) > 0 else ""
                prompt = "{raw} {error}".format(raw=shared.chunk.raw, error=error).strip()
                response = self.model.run(
                    system_prompt=system_prompt,
                    messages=[self.model.UserMessage(text=prompt)]
                )
                response = parse_codeblock_to_dict(response, codeblock='yaml')
                meta = shared.chunk.meta.copy()
                _terms = Terms(**response).terms
                if _terms is not None:
                    terms = [
                        Term(
                            term=term.term, 
                            type=term.type, 
                            evidence=term.evidence, 
                            explanation=term.explanation,
                            document_id=shared.chunk.document_id, 
                            longterm_id=shared.chunk.id,
                            meta=meta
                        )
                        for term in _terms if term is not None
                        ]
                    self.db.create_terms(terms=terms, session=Depends(get_session))
                return shared
            except Exception as e:
                errors.append(str(e))

    def run(self, shared:Shared):
        self.model.model_name = shared.term_model
        self.fallback(
            system_prompt=read_system_prompt(shared.term_system_prompt),
            shared=shared
        )
        return shared
    
class Parallel(Action):
    """Executes multiple actions concurrently using asyncio for parallel processing."""
    def __init__(self, actions:List[Action]):
        super().__init__()
        self.actions = actions

    def run(self, shared:Shared):
        """Execute multiple actions in parallel using asyncio.
        
        This method enables parallel execution of synchronous actions by:
        1. Using nest_asyncio to allow asyncio.run() in Jupyter/existing event loops
        2. Wrapping synchronous action.run() calls in async functions
        3. Using asyncio.gather() to run all tasks concurrently
        
        Why this works:
        - nest_asyncio.apply() patches asyncio to allow nested event loops
        - run_action() converts sync calls to async coroutines
        - asyncio.gather() executes all coroutines concurrently, not sequentially
        - The shared object is passed to each action, allowing state sharing
        
        Args:
            shared: Shared state object passed to all parallel actions
            
        Returns:
            Shared: The same shared object after all actions complete
        """
        import nest_asyncio
        nest_asyncio.apply()
        
        async def run_parallel():
            async def run_action(action:Action):
                return action.run(shared)
            tasks = [run_action(action) for action in self.actions]
            await asyncio.gather(*tasks)
        
        asyncio.run(run_parallel())
        return shared