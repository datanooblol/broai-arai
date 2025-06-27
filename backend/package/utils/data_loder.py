from broai.experiments.pdf_to_markdown import pdf_to_markdown
from broai.experiments.chunk import split_markdown, consolidate_markdown, get_markdown_sections, split_overlap
from broai.interface import Context
from package.interface import SourceOptions
from docling.document_converter import DocumentConverter


class PDFLoader:
    def __init__(self, source: SourceOptions, max_tokens=500, overlap=int(500*0.3)):
        self.source = source
        self.max_tokens = max_tokens
        self.overlap = overlap

    def load(self, source:SourceOptions):
        converter = DocumentConverter()
        result = converter.convert(source.path)
        text = result.document.export_to_markdown()  # output: "## Docling Technical Report[...]"
        # text, image = pdf_to_markdown(source.path)
        return text

    def chunk(self, source:SourceOptions, text, max_tokens, overlap):
        chunks = split_markdown(text)
        consolidated_chunks = consolidate_markdown(chunks)
        sections = get_markdown_sections(consolidated_chunks)
        contexts = []
        for section, chunk in zip(sections, consolidated_chunks):
            contexts.append(
                Context(context=chunk, metadata={"section": section, "source": source.path, "type": source.type})
            )
        new_contexts = split_overlap(contexts, max_tokens=max_tokens, overlap=overlap)
        return new_contexts
    
    def run(self):
        text = self.load(self.source)
        chunks = self.chunk(self.source, text, max_tokens=self.max_tokens, overlap=self.overlap)
        return chunks
    