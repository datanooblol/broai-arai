from broflow import Action, Flow, Start, End
from dataclasses import dataclass, field
from typing import Optional, List
import asyncio
import time

@dataclass
class Shared:
    a_result:Optional[str] = None
    b_result:Optional[str] = None

class A(Action):
    async def run(self, shared:Shared):
        await asyncio.sleep(2)
        shared.a_result = "Done"
        return shared
    
class B(Action):
    async def run(self, shared:Shared):
        await asyncio.sleep(5)
        shared.b_result = "Done"
        return shared

class Parallel(Action):
    """In this class how can I run asyncio to make two action run in parallel"""
    def __init__(self, actions:List[Action]):
        super().__init__()
        self.actions = actions

    def run(self, shared:Shared):
        import nest_asyncio
        nest_asyncio.apply()
        async def run_parallel():
            tasks = [action.run(shared) for action in self.actions]
            await asyncio.gather(*tasks)
        asyncio.run(run_parallel())
        return shared
    
if __name__=='__main__':
    shared = Shared()

    a_action = A()
    b_action = B()
    par_actions = Parallel(actions=[a_action, b_action])
    start_action = Start(message="Start Test")
    end_action = End(message="End Test")

    start_action >> par_actions >> end_action
    flow = Flow(start_action=start_action, name="Mock Test")
    
    start_time = time.time()
    flow.run(shared)
    print(shared)

    end_time = time.time()

    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"A result: {shared.a_result}")
    print(f"B result: {shared.b_result}")    