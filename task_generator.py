
import random


def generate_tasks(n, minimum=100, maximum=1000, seed=None):
    if n < 1:
        raise ValueError("Number of tasks must be positive.")
    if minimum < 1 or maximum < minimum:
        raise ValueError("Task length range must be valid and positive.")

    generator = random.Random(seed)
    tasks = []
    for i in range(n):
        length = generator.randint(minimum, maximum)
        priority = generator.randint(1, 5)
        deadline = generator.randint(maximum + 50, maximum * 3)
        tasks.append({
            "task_id": f"T{i+1}",
            "length": length,
            "priority": priority,
            "deadline": deadline,
            "description": f"Compute job {i+1}",
            "status": "Queued"
        })
    return tasks
