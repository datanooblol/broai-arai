# the experiment will be done item by item
# it means if we have 20 items, we will run the whole flow 20 times
import re
import json
from rouge_score import rouge_scorer
from broflow import Action
from brollm import BaseLLM
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Literal
from package.databases.session import Depends, get_session
from package.databases.management.longterm import LongTermManagement, LongTerm
from package.databases.management.document import DocumentManagement, Document
from package.databases.management.term import TermManagement, Term
from package.embedding.baai import BAAIEmbedding
from package.cross_encoder.cross_encoder import ReRanker
from broprompt import parse_codeblock_to_dict
from collections import Counter
import string

@dataclass
class Shared:
    # setup
    question:str
    answer:str
    type:str
    source:str
    experiment_id:str
    experiment_set:str
    # experiment:str
    experiment_storage: str
    document_id: Optional[str] = None
    document_source: Optional[str] = None

    # debug
    chat_system_prompt: str = "You're a helpful assistant"
    chat_message_prompt: Optional[str] = None
    potential_terms:list = field(default_factory=list)
    detailed_terms:dict = field(default_factory=dict)
    contexts:List[str] = field(default_factory=list)
    evaluation:dict = field(default_factory=dict)
    predict: Optional[str] = None
    
    # control experiment
    chat_model:Optional[str] = None
    chat_system_prompt_path:Optional[str] = None
    term_detector_model:Optional[str] = None
    term_detector_system_prompt_path:Optional[str] = None
    embed_method: Literal['raw', 'enrich', 'combo'] = 'raw'
    is_term:Literal['skip', 'evidence', 'explanation', 'both'] = 'skip'
    is_context:bool = False
    is_rerank:bool = False

class Router(Action):
    def __init__(self, retriever:DocumentManagement):
        super().__init__()
        self.retriever = retriever

    def setup_experiment(self, shared:Shared):
        document = self.retriever.read_document_by_source(shared.source, session=Depends(get_session))
        shared.document_source = document.source
        shared.document_id = document.id
        with open(shared.chat_system_prompt_path, 'r') as f:
            system_prompt = f.read()
        shared.chat_system_prompt = system_prompt
        return shared
    
    def router_logic(self, shared:Shared):
        term = shared.is_term
        context = shared.is_context
        if term == 'skip' and context is False:
            return "default"
        if term == 'skip' and context is True:
            return "context_retriever"
        return "term_manager"
    
    def run(self, shared:Shared):
        shared = self.setup_experiment(shared)
        self.next_action = self.router_logic(shared)
        return shared
    
class TermManager(Action):
    def __init__(self, model:BaseLLM, retriever:TermManagement):
        super().__init__()
        self.model = model
        self.retriever = retriever

    def term_retriever_logic(self, shared:Shared):
        if shared.is_context is True:
            return "context_retriever"
        return "default"
    
    def get_potential_terms(self, shared:Shared):
        with open(shared.term_detector_system_prompt_path, 'r') as f:
            system_prompt = f.read()
        question = shared.question
        errors=[]
        for i in range(5):
            try:
                prompt = question
                if len(errors)>0:
                    prompt = "{question}\n\nAvoid below errors:\n\n{errors}\n\n".format(question=question, errors="\n".join(errors))
                potential_terms = self.model.run(
                    system_prompt=system_prompt,
                    messages=[self.model.UserMessage(text=prompt)]
                )
                potential_terms = parse_codeblock_to_dict(potential_terms, codeblock='json')['terms']
                return potential_terms
            except Exception as e:
                errors.append(str(e))
        return []

    def filter_valid_terms(self, source_term:str, terms:List[Term]):
        """add in forth evaluation"""
        selected_terms = []
        for term in terms:
            mask = True
            mask &= source_term.lower() != term.evidence.lower().strip()
            mask &= term is not None
            mask &= len(source_term.lower())*2 < len(term.evidence.replace("  ", "").strip().lower())
            if mask:
                selected_terms.append({"evidence":term.evidence, "explanation":term.explanation})
        return selected_terms

    def get_detailed_terms(self, shared:Shared):
        if len(shared.potential_terms) == 0:
            return {}
        detailed_terms = {}
        for term in shared.potential_terms:
            _term = term['term']
            confidence = term['confidence']
            similar_terms = self.retriever.read_similar_terms(term=_term, session=Depends(get_session), document_ids=[shared.document_id])
            # detailed_terms[_term] = [{"evidence":st.evidence, "explanation":st.explanation} for st in similar_terms if st]
            detailed_terms[_term] = self.filter_valid_terms(_term, similar_terms)
        return detailed_terms
    
    def run(self, shared:Shared):
        self.model.model_name = shared.term_detector_model
        shared.potential_terms = self.get_potential_terms(shared)
        shared.detailed_terms = self.get_detailed_terms(shared)
        self.next_action = self.term_retriever_logic(shared)
        return shared

class ContextRetriever(Action):
    def __init__(self, retriever:LongTermManagement, embedder:BAAIEmbedding, reranker:ReRanker):
        super().__init__()
        self.embedder = embedder
        self.retriever = retriever
        self.reranker = reranker

    def run(self, shared:Shared):
        vector = self.embedder.run([shared.question])[0]
        longterms = self.retriever.read_similar_text_with_like_source(
            vector, 
            embed_method=shared.embed_method, 
            session=Depends(get_session), 
            sources=[shared.document_source]
        )
        if shared.is_rerank is True:
            longterms, _ = self.reranker.run(
                search_query=shared.question,
                longterms=longterms,
                embed_method=shared.embed_method,
            )
        shared.contexts = [lt.__dict__.get(shared.embed_method, "") for lt in longterms]
        return shared

class Chat(Action):
    def __init__(self, model:BaseLLM):
        super().__init__()
        self.model = model

    def extract_detail_term(self, shared:Shared):
        is_term = shared.is_term
        prompt = []
        for term, details in shared.detailed_terms.items():
            _prompt = ["TERM found: {term}".format(term=term)]
            for detail in details:
                evidence = "Evidence found: {detail}".format(detail=detail.get("evidence"))
                explanation = "Explanation: {detail}".format(detail=detail.get("explanation"))
                if is_term=='evidence':
                    _prompt.append("\t- {ev}".format(ev=evidence))
                elif is_term=='explanation':
                    _prompt.append("\t- {ex}".format(ex=explanation))
                else:
                    _prompt.append("\t- {ev} with Possible {ex}".format(ev=evidence, ex=explanation))
            prompt.append("\n".join(_prompt))
        return prompt

    def get_user_message(self, shared:Shared):
        prompt = []
        if shared.is_term != 'skip':
            prompt.append(
                "TERMS:\n\n{detail}\n\n".format(detail="\n".join(self.extract_detail_term(shared)))
            )
        if shared.is_context is True:
            prompt.append(
                "CONTEXTS:\n\n{detail}\n\n".format(detail="\n".join(["<|start_context|>{ctx}<|end_context|>".format(ctx=ctx.strip()) for ctx in shared.contexts]))
            )
        prompt.append(
            "QUESTION:\n\n{question}\n\n".format(question=shared.question)
        )
        return "".join(prompt)
    
    def run(self, shared:Shared):
        self.model.model_name = shared.chat_model
        message = self.get_user_message(shared)
        predict = self.model.run(
            system_prompt=shared.chat_system_prompt,
            messages=[self.model.UserMessage(text=message)]
        )
        shared.chat_message_prompt = message
        shared.predict = predict
        return shared
    
class Evaluator(Action):
    def __init__(self):
        super().__init__()
        self.metrics = ['rouge1', 'rouge2', 'rougeL', 'rougeLsum']
        self.scorer = rouge_scorer.RougeScorer(rouge_types=self.metrics, use_stemmer=True)
    
    def preprocess_text(self, text):
        if not text:
            return ""
        text = text.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def normalize_answer(self, s):
        def remove_articles(text):
            return re.sub(r'\b(a|an|the)\b', ' ', text)
        def remove_punc(text):
            return ''.join(ch for ch in text if ch not in string.punctuation)
        def white_space_fix(text):
            return ' '.join(text.split())
        return white_space_fix(remove_articles(remove_punc(s.lower())))
    
    def hotpot_scores(self, prediction, ground_truth):
        norm_pred = self.normalize_answer(prediction)
        norm_gt = self.normalize_answer(ground_truth)
        
        # Exact Match
        em = float(norm_pred == norm_gt)
        
        # F1 Score
        pred_tokens = norm_pred.split()
        gt_tokens = norm_gt.split()
        common = Counter(pred_tokens) & Counter(gt_tokens)
        num_same = sum(common.values())
        
        if num_same == 0:
            return {'em': em, 'f1': 0.0, 'precision': 0.0, 'recall': 0.0}
        
        precision = num_same / len(pred_tokens)
        recall = num_same / len(gt_tokens)
        f1 = (2 * precision * recall) / (precision + recall)
        
        return {'em': em, 'f1': f1, 'precision': precision, 'recall': recall}
    
    def get_score(self, shared: Shared):
        # ROUGE scores
        ground_truth = self.preprocess_text(shared.answer)
        predict = self.preprocess_text(shared.predict)
        rouge_score = self.scorer.score(target=ground_truth, prediction=predict)
        
        _score = {}
        for metric in self.metrics:
            _score[metric] = dict(
                precision=rouge_score[metric].precision,
                recall=rouge_score[metric].recall,
                fmeasure=rouge_score[metric].fmeasure
            )
        
        # HotpotQA scores
        _score['hotpot'] = self.hotpot_scores(shared.predict, shared.answer)
        
        return _score
    
    def run(self, shared:Shared):
        shared.evaluation = self.get_score(shared)
        _shared = asdict(shared)
        import os
        os.makedirs(os.path.dirname(shared.experiment_storage), exist_ok=True)        
        with open(shared.experiment_storage, 'w') as f:
            json.dump(_shared, f, indent=4)
        return shared    
