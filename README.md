
# Cloud Task Operations Dashboard

## Run Project
1. Create/activate a virtual environment if needed.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Features
- Login with the seeded account `admin` / `admin`.
- Dashboard, user management, task submission, virtual machines, scheduling, results, and algorithm comparison screens.
- SQLite persistence in `cloud_task_scheduler/database/scheduler.db`.
- Balanced, priority, deadline, shortest-job, cost-optimized, and random strategies.
- Deadline compliance, makespan, throughput, utilization, and estimated cost metrics.
- Excel export for the latest scheduling run.

## Using the dashboard

Set the task count, scheduler, seed, and live delay, then select **Run Live**. The VM and task tables update as allocations happen. Use **Pause**, **Resume**, or **Stop** while a run is active. **Export** lets you choose a separate Excel destination after a run.
