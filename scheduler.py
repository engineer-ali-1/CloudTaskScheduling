
import random

SUPPORTED_ALGORITHMS = [
    "Balanced Scheduler",
    "Priority Scheduler",
    "Deadline Scheduler",
    "Shortest Job First",
    "Cost Optimized Scheduler",
    "Random Scheduler"
]


def random_scheduler(tasks, vms):
    mapping = []
    generator = random.Random(42)
    for task in tasks:
        vm = generator.choice(vms)
        vm.assign_task(task)
        mapping.append(_build_mapping(task, vm))
    return mapping


def balanced_scheduler(tasks, vms):
    mapping = []
    sorted_tasks = sorted(tasks, key=lambda item: item["length"], reverse=True)
    for task in sorted_tasks:
        vm = min(vms, key=lambda candidate: candidate.estimated_finish_time() + task["length"] / candidate.mips)
        vm.assign_task(task)
        mapping.append(_build_mapping(task, vm))
    return mapping


def priority_scheduler(tasks, vms):
    mapping = []
    sorted_tasks = sorted(tasks, key=lambda item: (-item["priority"], item["deadline"]))
    for task in sorted_tasks:
        vm = min(vms, key=lambda candidate: candidate.estimated_finish_time() + task["length"] / candidate.mips)
        vm.assign_task(task)
        mapping.append(_build_mapping(task, vm))
    return mapping


def deadline_scheduler(tasks, vms):
    mapping = []
    sorted_tasks = sorted(tasks, key=lambda item: item["deadline"])
    for task in sorted_tasks:
        vm = min(vms, key=lambda candidate: candidate.estimated_finish_time() + task["length"] / candidate.mips)
        vm.assign_task(task)
        mapping.append(_build_mapping(task, vm))
    return mapping


def shortest_job_scheduler(tasks, vms):
    mapping = []
    for task in sorted(tasks, key=lambda item: (item["length"], -item["priority"])):
        vm = min(vms, key=lambda candidate: candidate.estimated_finish_time() + task["length"] / candidate.mips)
        vm.assign_task(task)
        mapping.append(_build_mapping(task, vm))
    return mapping


def cost_optimized_scheduler(tasks, vms):
    mapping = []
    for task in sorted(tasks, key=lambda item: (item["deadline"], -item["priority"])):
        vm = min(vms, key=lambda candidate: (
            (candidate.estimated_finish_time() + task["length"] / candidate.mips) / candidate.mips
        ))
        vm.assign_task(task)
        mapping.append(_build_mapping(task, vm))
    return mapping


def schedule_tasks(tasks, vms, algorithm):
    if algorithm == "Random Scheduler":
        return random_scheduler(tasks, vms)
    if algorithm == "Balanced Scheduler":
        return balanced_scheduler(tasks, vms)
    if algorithm == "Priority Scheduler":
        return priority_scheduler(tasks, vms)
    if algorithm == "Deadline Scheduler":
        return deadline_scheduler(tasks, vms)
    if algorithm == "Shortest Job First":
        return shortest_job_scheduler(tasks, vms)
    if algorithm == "Cost Optimized Scheduler":
        return cost_optimized_scheduler(tasks, vms)
    raise ValueError(f"Unknown algorithm: {algorithm}")


def schedule_tasks_stream(tasks, vms, algorithm):
    ordered_tasks = list(tasks)
    if algorithm == "Balanced Scheduler":
        ordered_tasks.sort(key=lambda item: item["length"], reverse=True)
    elif algorithm == "Priority Scheduler":
        ordered_tasks.sort(key=lambda item: (-item["priority"], item["deadline"]))
    elif algorithm == "Deadline Scheduler":
        ordered_tasks.sort(key=lambda item: item["deadline"])
    elif algorithm == "Shortest Job First":
        ordered_tasks.sort(key=lambda item: (item["length"], -item["priority"]))
    elif algorithm == "Cost Optimized Scheduler":
        ordered_tasks.sort(key=lambda item: (item["deadline"], -item["priority"]))
    elif algorithm != "Random Scheduler":
        raise ValueError(f"Unknown algorithm: {algorithm}")

    random_generator = random.Random(42)
    for task in ordered_tasks:
        if algorithm == "Random Scheduler":
            vm = random_generator.choice(vms)
        else:
            vm = min(vms, key=lambda candidate: candidate.estimated_finish_time() + task["length"] / candidate.mips)
        vm.assign_task(task)
        yield _build_mapping(task, vm)


def _build_mapping(task, vm):
    start_time = vm.estimated_finish_time()
    completion_time = start_time + task["length"] / vm.mips
    return {
        "task_id": task["task_id"],
        "task_length": task["length"],
        "priority": task["priority"],
        "deadline": task["deadline"],
        "description": task["description"],
        "status": task.get("status", "Queued"),
        "vm_id": vm.vm_id,
        "vm_mips": vm.mips,
        "vm_ram": vm.ram,
        "vm_load": vm.total_load(),
        "start_time": round(start_time, 3),
        "completion_time": round(completion_time, 3),
        "deadline_met": completion_time <= task["deadline"],
        "slack": round(task["deadline"] - completion_time, 3)
    }


def calculate_metrics(mapping, vms):
    makespan = max((vm.estimated_finish_time() for vm in vms), default=0)
    total_length = sum(item["task_length"] for item in mapping)
    deadline_met = sum(1 for item in mapping if item["deadline_met"])
    return {
        "task_count": len(mapping),
        "total_length": total_length,
        "makespan": round(makespan, 3),
        "throughput": round(len(mapping) / makespan, 4) if makespan else 0,
        "deadline_met": deadline_met,
        "deadline_rate": round(deadline_met / len(mapping) * 100, 2) if mapping else 0,
        "peak_load": round(max((vm.total_load() for vm in vms), default=0), 3),
        "estimated_cost": round(sum(vm.estimated_cost() for vm in vms), 4)
    }
