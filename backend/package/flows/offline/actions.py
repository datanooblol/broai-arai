from broflow import Action
from dataclasses import dataclass, field

@dataclass
class Shared:
    previous_action:str

class Load(Action):
    """Load data and store in document"""
    def run(self, shared:Shared):
        return shared
    
class Chunk(Action):
    """Chunk the document into smaller subset and store in longterm"""
    def run(self, shared:Shared):
        return shared

class Enrich(Action):
    """Enrich with parallel calling and store in longterm"""
    def run(self, shared:Shared):
        return shared
    
class Jargon(Action):
    """Jargon with parallel calling and store in term"""
    def run(self, shared:Shared):
        return shared
    
class Embed(Action):
    """Embed all vectors at once and store in longterm"""
    def run(self, shared:Shared):
        return shared