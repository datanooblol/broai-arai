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

    def run(self, contexts):
        ...