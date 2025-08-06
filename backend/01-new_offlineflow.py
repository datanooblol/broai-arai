from dataclasses import dataclass, field
from typing import List, Optional
import pickle
from package.flows.offline.flow import get_parallel_actions, Shared
from package.interface import SourceOptions
from package.utils.data_loder import PDFLoader
from package.databases.session import get_session, Depends
from package.databases.management.document import DocumentManagement, Document
from package.databases.management.longterm import LongTermManagement, LongTerm
from tqdm import tqdm

def create_document(source_path:str):
    dm = DocumentManagement()
    ltm = LongTermManagement()
    source_type = source_path.split(".")[-1]

    source_ops = SourceOptions(
        path=source_path,
        type=source_type if source_type in ['pdf'] else "other"
    )
    document = Document(source=source_path, type=source_type)
    document = dm.create_document(document, session=Depends(get_session))

    contexts = PDFLoader(source=source_ops).run()
    longterms = [LongTerm(document_id=document.id, raw=context.context, meta=context.metadata) for context in contexts]
    ltm.create_raws(longterms, session=Depends(get_session))

    _longterms = ltm.read_longterms_by_document(document_id=document.id, session=Depends(get_session))
    longterms = []
    for l in _longterms:
        _l = l.__dict__.copy()
        if hasattr(_l, '_sa_instance_state'):
            delattr(_l, '_sa_instance_state')
        longterms.append(LongTerm(**_l))

    return document, longterms

@dataclass
class OfflineIndexRunner:
    content_path: str
    enrich_system_prompt: str = './package/flows/offline/prompts/enricher.md'
    term_system_prompt: str = './package/flows/offline/prompts/term_extractor.md'
    term_model:str = 'us.meta.llama4-maverick-17b-instruct-v1:0'
    chunks: List[LongTerm] = field(default_factory=list)
    current_chunk_index: int = 0
    completed_count: int = 0
    state_path: str = './offline_index_state.pkl'
    document_id: Optional[str] = None
    document_source: Optional[str] = None
    
    def load_content(self):
        document, longterms = create_document(self.content_path)
        self.document_id = document.id
        self.document_source = document.source
        self.chunks.extend(longterms)

    def run(self):
        if len(self.chunks)==0:
            self.load_content()
        try:
            for i in tqdm(range(self.current_chunk_index, len(self.chunks))):
                # print("{epoch}/{total}".format(epoch=i+1, total=len(self.chunks)))
                self.current_chunk_index = i
                chunk = self.chunks[i]
                
                # Process single chunk: Parallel(Enrich, Jargon) + Embed
                shared = Shared(
                    enrich_system_prompt=self.enrich_system_prompt,
                    term_system_prompt=self.term_system_prompt,
                    term_model=self.term_model,
                    chunk=chunk
                )
                flow = get_parallel_actions()
                flow.run(shared)
                self.completed_count += 1
                
        except KeyboardInterrupt:
            print("Interrupted by user. Saving state...")
            self.save_state()
            print(f"State saved. Completed {self.completed_count} tasks.")
            raise                
        except Exception as e:
            print("Error:", str(e))
            self.save_state()
            raise  

    def save_state(self):
        with open(self.state_path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load_state(cls, state_path=None):
        path = state_path or './offline_index_state.pkl'
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError as e:
            print("Error:", str(e))
            return None


if __name__=='__main__':
    from pathlib import Path
    import os
    
    source_dir = Path("./sources")
    pdf_files = list(source_dir.glob("*.pdf"))
    state_dir = Path("./experiments/offline/state/v1")
    
    # Check which files are already completed
    completed = []
    for pdf_path in pdf_files:
        state_file = pdf_path.stem.lower().replace("-",'_').replace(" ", "_")
        state_path = state_dir / f"{state_file}.pkl"
        if state_path.exists():
            runner = OfflineIndexRunner.load_state(str(state_path))
            if runner and runner.current_chunk_index >= len(runner.chunks) - 1:
                completed.append(pdf_path.name)
    
    print(f"Found {len(completed)} completed files, {len(pdf_files) - len(completed)} remaining")
    
    errors = []
    for pdf_path in tqdm(pdf_files):
        if pdf_path.name in completed:
            continue
            
        state_file = pdf_path.stem.lower().replace("-",'_').replace(" ", "_")
        state_path = str(state_dir / f"{state_file}.pkl")
        
        print(f"Processing: {pdf_path.name}")
        try:
            # Try to load existing state first
            runner = OfflineIndexRunner.load_state(state_path)
            if not runner:
                runner = OfflineIndexRunner(
                    content_path=str(pdf_path),
                    state_path=state_path
                )
            runner.run()
        except Exception as e:
            errors.append(dict(
                filename=pdf_path.name,
                statename=state_file,
                error=str(e)
            ))
            print(f"ERROR: {pdf_path.name} - {str(e)}")