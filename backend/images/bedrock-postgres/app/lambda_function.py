from package.databases.management.longterm import LongTermManagement
from package.databases.session import get_session, Depends
from package.databases.models.longterm import LongTerm
from package.llm.ollama import BedrockOllamaChat

def lambda_handler(event, context):
    model_name = event.get("model_name", "us.meta.llama3-2-11b-instruct-v1:0")
    model = BedrockOllamaChat(model_name=model_name)
    ltm = LongTermManagement()
    longterm_id = event.get("longterm_id", None)
    longterm:LongTerm = ltm.read_longterm(longterm_id=longterm_id, session=Depends(get_session))
    text = f"CONTEXT:\n\n{longterm.raw}\n\nINSTRUCTION: \n\nSummarize the above context and provide a concise overview of the key points."
    messages = [model.UserMessage(text=text)]
    system_prompt = "You are a helpful assistant that summarizes long-term memory content. Your task is to provide a concise and accurate summary of the provided context."
    response = model.run(system_prompt=system_prompt, messages=messages)
    longterm.enrich = response
    longterm.combo = f"{longterm.enrich}\n\n{longterm.raw}"
    ltm.update_longterms(longterms=[longterm], session=Depends(get_session))
    return {
        "processed": longterm_id
    }