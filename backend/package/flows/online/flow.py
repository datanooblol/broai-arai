from broflow import Start, End, Flow
from .actions import Router, TermManager, ContextRetriever, Chat, Evaluator, Shared
from package.databases.management.longterm import LongTermManagement, LongTerm
from package.databases.management.document import DocumentManagement, Document
from package.databases.management.term import TermManagement, Term
from package.embedding.baai import BAAIEmbedding
from package.cross_encoder.cross_encoder import ReRanker
from brollm import BedrockChat

model = BedrockChat()
reranker = ReRanker()
embedder = BAAIEmbedding()

ltm = LongTermManagement()
dm = DocumentManagement()
tm = TermManagement()

def get_online_flow(experiment):
    start_action = Start(message="Start {experiment}".format(experiment=experiment))
    end_action = End(message="End {experiment}".format(experiment=experiment))
    router_action = Router(retriever=dm)
    term_manager = TermManager(
        model=model,
        retriever=tm
    )
    context_retriever = ContextRetriever(
        retriever=ltm,
        embedder=embedder,
        reranker=reranker
    )
    chat_action = Chat(
        model=model
    )
    evaluator_action = Evaluator()

    start_action >> router_action >> chat_action
    router_action - "context_retriever" >> context_retriever
    router_action - "term_manager" >> term_manager
    term_manager - "context_retriever" >> context_retriever
    context_retriever >> chat_action
    term_manager >> chat_action
    chat_action >> evaluator_action >> end_action

    flow = Flow(start_action, name="Flow {experiment}".format(experiment=experiment))
    return flow