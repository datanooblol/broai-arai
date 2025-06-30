from package.databases.management.longterm import LongTermManagement
from package.databases.session import get_session, Depends
from package.databases.models.longterm import LongTerm
from package.agents.context_enricher import ContextEnricher
from package.agents.jargon_extractor import JargonExtractor
from package.databases.models.jargon import Jargon
from package.databases.management.jargon import JargonManagement

def lambda_handler(event, context):
    context_enricher = ContextEnricher()
    jm = JargonManagement()
    ltm = LongTermManagement()
    jargon_extractor = JargonExtractor()
    document_id = event.get("document_id")
    longterm_id = event.get("longterm_id")    
    longterm:LongTerm = ltm.read_longterm(longterm_id=longterm_id, session=Depends(get_session))
    context = longterm.raw
    meta = longterm.meta
    summary = context_enricher.run(context=context)
    longterm.enrich = summary.summary
    longterm.combo = f"{longterm.enrich}\n\n{longterm.raw}"
    ltm.update_longterms(longterms=[longterm], session=Depends(get_session))
    _jargons = jargon_extractor.run(context=context)
    if _jargons is not None:
        jargons = [Jargon(jargon=jargon.jargon, evidence=jargon.evidence, explanation=jargon.explanation, document_id=document_id, meta=meta) for jargon in _jargons]
        jm.create_jargons(jargons=jargons, session=Depends(get_session))
    return {
        "processed": longterm_id,
        "document_id": document_id
    }