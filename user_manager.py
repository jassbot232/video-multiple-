from typing import Dict, List
import asyncio

class UserManager:
    def __init__(self):
        self.user_queues: Dict[int, List[dict]] = {}
        self.user_states: Dict[int, str] = {}
        self.progress_trackers: Dict[int, Dict] = {}
        self.locks: Dict[int, asyncio.Lock] = {}
    
    def get_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self.locks:
            self.locks[user_id] = asyncio.Lock()
        return self.locks[user_id]
    
    def set_user_state(self, user_id: int, state: str):
        self.user_states[user_id] = state
    
    def get_user_state(self, user_id: int) -> str:
        return self.user_states.get(user_id, "idle")
    
    def add_to_queue(self, user_id: int, task: dict):
        if user_id not in self.user_queues:
            self.user_queues[user_id] = []
        self.user_queues[user_id].append(task)
    
    def get_queue(self, user_id: int) -> List[dict]:
        return self.user_queues.get(user_id, [])
    
    def clear_queue(self, user_id: int):
        if user_id in self.user_queues:
            self.user_queues[user_id].clear()
    
    def update_progress(self, user_id: int, progress: float, status: str):
        if user_id not in self.progress_trackers:
            self.progress_trackers[user_id] = {}
        self.progress_trackers[user_id] = {
            'progress': progress,
            'status': status,
            'timestamp': asyncio.get_event_loop().time()
        }
    
    def get_progress(self, user_id: int) -> Dict:
        return self.progress_trackers.get(user_id, {'progress': 0, 'status': 'Idle'})

user_manager = UserManager()
