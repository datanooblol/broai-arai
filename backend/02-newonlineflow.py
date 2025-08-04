from typing import List
import pickle
from package.flows.online.flow import get_online_flow, Shared
from uuid import uuid4
from broflow import state
from dataclasses import dataclass
import json

def get_trainset():

    with open("./dataset/trainset.json", 'r', encoding='utf-8') as f:
        trainset = json.load(f)   
    for ts in trainset:
        ts['metadata']['source'] = ts['metadata']['source'].replace(":", "")         
    return trainset

def generate_experiments(
    embed_methods=['raw'],
    chat_system_prompt_paths=['./package/flows/online/prompts/v1/chat.md'],
    term_detector_system_prompt_paths=["./package/flows/online/prompts/term_detector.md"],
    chat_models=[
            "us.meta.llama3-2-11b-instruct-v1:0",
        ],
    term_detector_models=["us.meta.llama3-2-11b-instruct-v1:0"],
    is_terms = ['skip', 'evidence', 'explanation', 'both']
):
    from itertools import product
    
    is_contexts = [True, False]
    
    experiments = []
    for (embed_method, chat_prompt, term_prompt, chat_model, term_model, 
         is_term, is_context) in product(
        embed_methods, chat_system_prompt_paths, term_detector_system_prompt_paths,
        chat_models, term_detector_models, is_terms, is_contexts
    ):
        base_config = {
            "embed_method": embed_method,
            "chat_system_prompt_path": chat_prompt,
            "term_detector_system_prompt_path": term_prompt,
            "chat_model": chat_model,
            "term_detector_model": term_model,
            "is_term": is_term,
            "is_context": is_context
        }
        
        if is_context:
            experiments.extend([
                {**base_config, "is_rerank": False},
                {**base_config, "is_rerank": True}
            ])
        else:
            experiments.append({**base_config, "is_rerank": False})
    
    return experiments

@dataclass
class ControlExperiment:
    chat_model:str
    chat_system_prompt_path:str
    term_detector_model:str
    term_detector_system_prompt_path:str
    embed_method:str
    is_term:str
    is_context:bool
    is_rerank:bool
    experiment_set:str

def one_experiment(ts, con_exp:ControlExperiment,):
    _id = str(uuid4())
    experiment_storage = "./experiments/evaluations/{file}.json".format(file=_id)
    shared = Shared(
        experiment_id=_id,
        experiment_set=con_exp.experiment_set,
        question=ts['question'],
        answer=ts['answer'],
        type=ts['type'],
        source=ts['metadata']['source'],
        chat_model=con_exp.chat_model,
        term_detector_model=con_exp.term_detector_model,
        chat_system_prompt_path=con_exp.chat_system_prompt_path,
        term_detector_system_prompt_path=con_exp.term_detector_system_prompt_path,
        experiment_storage=experiment_storage,
        embed_method=con_exp.embed_method,
        is_term=con_exp.is_term,
        is_context=con_exp.is_context,
        is_rerank=con_exp.is_rerank

    )
    flow = get_online_flow(experiment=shared.experiment_id)
    flow.run(shared)

@dataclass
class ExperimentRunner:
    experiments: List[dict]
    trainset: List[dict]
    current_experiment_index: int = 0
    current_trainset_index: int = 0
    completed_count: int = 0
    failed_count: int = 0
    experiment_path:str = './experiments/experiment_state.pkl'

    def run(self):
        total_exp = len(self.experiments)
        total_train = len(self.trainset)
        try:
            for i in range(self.current_experiment_index, len(self.experiments)):
                self.current_experiment_index = i
                experiment = self.experiments[i]
                experiment.update({"experiment_set":str(uuid4())})
                con_exp = ControlExperiment(**experiment)                
                for j in range(self.current_trainset_index, len(self.trainset)):
                    print("running | experiment: {a}/{b} | trainset: {c}/{d}".format(
                        a=self.current_experiment_index+1, b=total_exp,
                        c=self.current_trainset_index+1, d=total_train
                    ))
                    self.current_trainset_index = j
                    one_experiment(self.trainset[j], con_exp)
                    self.completed_count += 1
                
                self.current_trainset_index = 0
                
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
        with open(self.experiment_path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load_state(cls):
        try:
            with open(cls.experiment_path, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError as e:
            print("Error:", str(e))
            return None

if __name__=='__main__':
    state.set('debug', False)
    exp_runner = ExperimentRunner.load_state()
    if exp_runner is None:
        experiments = generate_experiments(
            embed_methods=['raw'],
            chat_system_prompt_paths=['./package/flows/online/prompts/v1/chat.md'],
            term_detector_system_prompt_paths=["./package/flows/online/prompts/term_detector.md"],
            is_terms=['both'],
            chat_models=[
                # "us.meta.llama3-2-1b-instruct-v1:0",
                "us.meta.llama3-2-11b-instruct-v1:0",
                "us.meta.llama4-maverick-17b-instruct-v1:0",
                "us.meta.llama4-scout-17b-instruct-v1:0",
                # "meta.llama3-3-70b-instruct-v1:0",
                # "us.meta.llama3-2-90b-instruct-v1:0",
            ],
            term_detector_models=["us.meta.llama3-2-11b-instruct-v1:0"]
        )        
        trainset = get_trainset()
        exp_runner = ExperimentRunner(experiments=experiments, trainset=trainset)
    exp_runner.run()
    print("Evaluation successfully")