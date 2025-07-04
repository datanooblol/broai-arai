from package.databases.models.longterm import LongTerm

class OfflineFlow:
    def __init__(self, memory=None):
        self.memory = memory

    def enrich(self):
        """distributed enrichment"""
        ...

    def extract_jargons(self):
        """distributed jargon extraction"""
        ...

    def embed(self):
        ...

    def run(self, document_id, contexts):
        longterms = [
            LongTerm(
                document_id=document_id,
                raw=context.context,
                meta=context.metadata
            ) 
            for context in contexts
        ]
        return longterms
        # self.memory.longterm.create_raws(longterms)