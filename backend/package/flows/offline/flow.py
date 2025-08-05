from .actions import Enrich, Jargon, Embed, Parallel, Shared
from broflow import Flow, Start, End
from brollm import BedrockChat
from package.databases.management.longterm import LongTermManagement, LongTerm
from package.databases.management.term import TermManagement, Term

def get_parallel_actions():
    enrich_action = Enrich(model=BedrockChat(), db=LongTermManagement())
    jargon_action = Jargon(model=BedrockChat(), db=TermManagement())
    return Parallel(actions=[enrich_action, jargon_action])