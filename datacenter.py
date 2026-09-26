
class VirtualMachine:
    def __init__(self, vm_id, mips, ram=512):
        self.vm_id = vm_id
        self.mips = mips
        self.ram = ram
        self.tasks = []

    def assign_task(self, task):
        self.tasks.append(task)

    def total_tasks(self):
        return len(self.tasks)

    def total_load(self):
        return sum(task["length"] for task in self.tasks)

    def estimated_finish_time(self):
        if self.mips <= 0:
            return float("inf")
        return self.total_load() / self.mips

    def utilization(self, makespan=None):
        if makespan is None:
            makespan = self.estimated_finish_time()
        if makespan <= 0:
            return 0.0
        return min(100.0, self.estimated_finish_time() / makespan * 100)

    def estimated_cost(self, rate_per_hour=0.12):
        return self.estimated_finish_time() / 3600 * rate_per_hour

    def clear_tasks(self):
        self.tasks = []
