# 간단한 인메모리 상태 저장소
# 실무에서는 Redis 등을 사용하지만 MVP에서는 메모리로 충분함

class TaskManager:
    def __init__(self):
        self.tasks = {}

    def create_task(self, task_id: str):
        self.tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "message": "Initializing...",
            "details": []
        }

    def update_task(self, task_id: str, status: str = None, progress: int = None, message: str = None):
        if task_id in self.tasks:
            if status:
                self.tasks[task_id]["status"] = status
            if progress is not None:
                self.tasks[task_id]["progress"] = progress
            if message:
                self.tasks[task_id]["message"] = message

    def add_detail(self, task_id: str, detail: str):
        if task_id in self.tasks:
            self.tasks[task_id]["details"].append(detail)

    def get_task(self, task_id: str):
        return self.tasks.get(task_id, None)

# 전역 인스턴스
task_manager = TaskManager()