from fastapi import FastAPI
import time
import asyncio
import random
from typing import Coroutine

app = FastAPI()

tasks: dict[asyncio.Task] = dict()


class TaskObj:
    def __init__(self, coroutine, eta = None):
        assert isinstance(coroutine, Coroutine)
        self.task = asyncio.create_task(coroutine)
        self.start_time = time.time()

        self.task.add_done_callback(self._update_elapsed_time)

        self._eta = eta
        self._elapsed_time = 0

        if eta is None:
            # returns elapsed time
            self.eta_func = self.elapsed_time
        else:
            # return eta
            self.eta_func = self.estimate


    def elapsed_time(self):
        if not self.is_done():
            self._update_elapsed_time()    
        return self._elapsed_time
    
    def _update_elapsed_time(self, *args):
        self._elapsed_time = time.time() - self.start_time
    
    def estimate(self):
        return self._eta - self.elapsed_time()

    def result(self): # ?
        if self.is_done():
            return self.task.result()
        else:
            return None
    
    def eta(self) -> float:
        if not self.is_done():
            return self.eta_func()
        else:
            return 0.0
    
    def is_done(self) -> bool:
        return self.task.done()
    
    def make_status_dict(self) -> dict:
        stat = dict()
        stat["is_done"] = self.is_done()
        if stat["is_done"]:
            stat["result"] = self.result()
        if self.eta is not None:
            stat["estimate"] = self.eta()
        stat["elapsed"] = self.elapsed_time()
        
        return stat


@app.get("/")
async def read_root():
    return {"Hello": str(asyncio.get_running_loop())}


@app.get("/start")
async def initiate_long_task(sec: float = 30):
    id = random.randint(0, 2 ** 32 - 1)

    # tasks[id] = asyncio.create_task(long_task_uninterruptable(sec))
    # time.sleep is blocking
    tasks[id] = TaskObj(asyncio.to_thread(time.sleep, sec), sec)

    return {"id": id}


@app.get("/status/{id}")
async def get_status(id: int):
    return tasks[id].make_status_dict()
