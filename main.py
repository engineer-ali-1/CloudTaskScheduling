"""Launch the Cloud Task Scheduler desktop application."""

from cloud_task_scheduler.main import App


if __name__ == '__main__':
    App().mainloop()

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import time

from datacenter import VirtualMachine
from task_generator import generate_tasks
from scheduler import calculate_metrics, schedule_tasks_stream, SUPPORTED_ALGORITHMS
from excel_writer import save_to_excel


class SchedulerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cloud Task Operations Dashboard")
        self.geometry("1360x860")
        self.configure(bg="#0b1220")
        self.minsize(1120, 720)
        self.resizable(True, True)

        self.vm_entries = []
        self.mapping = []
        self.vms = []
        self.tasks = []
        self.summary_values = {}
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.worker_thread = None
        self.run_token = 0
        self._build_interface()

    def _build_interface(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"), background="#111a2b", foreground="#f8fafc")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), background="#111a2b", foreground="#94a3b8")
        style.configure("Section.TFrame", background="#111a2b")
        style.configure("Card.TLabelframe", background="#182235", borderwidth=1, relief="solid", bordercolor="#2b3a52")
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 11, "bold"), background="#182235", foreground="#dbeafe")
        style.configure("Accent.TButton", foreground="#06131b", background="#2dd4bf", font=("Segoe UI", 10, "bold"), padding=8, borderwidth=0)
        style.map("Accent.TButton", background=[("active", "#5eead4"), ("disabled", "#334155")], foreground=[("disabled", "#94a3b8")])
        style.configure("Outline.TButton", foreground="#67e8f9", background="#182235", font=("Segoe UI", 10, "bold"), padding=8, borderwidth=1)
        style.map("Outline.TButton", background=[("active", "#24344d")], foreground=[("active", "#a5f3fc")])
        style.configure("TButton", font=("Segoe UI", 10), padding=6, foreground="#dbeafe", background="#24344d", borderwidth=0)
        style.map("TButton", background=[("active", "#334963"), ("disabled", "#1e293b")], foreground=[("disabled", "#64748b")])
        style.configure("TLabel", background="#111a2b", font=("Segoe UI", 10), foreground="#cbd5e1")
        style.configure("TEntry", padding=5, fieldbackground="#0f172a", foreground="#e2e8f0", bordercolor="#334155", insertcolor="#f8fafc")
        style.configure("TSpinbox", padding=4, fieldbackground="#0f172a", foreground="#e2e8f0", bordercolor="#334155", arrowcolor="#94a3b8")
        style.configure("TCombobox", padding=4, fieldbackground="#0f172a", foreground="#e2e8f0", selectbackground="#164e63", selectforeground="#ecfeff", arrowcolor="#94a3b8")
        style.map("TCombobox", fieldbackground=[("readonly", "#0f172a")], foreground=[("readonly", "#e2e8f0")])
        style.configure("Treeview", background="#0f172a", fieldbackground="#0f172a", foreground="#dbeafe", rowheight=27, font=("Segoe UI", 10), bordercolor="#2b3a52", lightcolor="#2b3a52", darkcolor="#2b3a52")
        style.map("Treeview", background=[("selected", "#155e75")], foreground=[("selected", "#ecfeff")])
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), foreground="#bae6fd", background="#22314a", relief="flat", padding=7)
        style.map("Treeview.Heading", background=[("active", "#2d4564")])
        style.configure("Horizontal.TProgressbar", troughcolor="#0f172a", background="#2dd4bf", bordercolor="#2b3a52", lightcolor="#2dd4bf", darkcolor="#2dd4bf")

        header_frame = ttk.Frame(self, style="Section.TFrame", padding=(20, 16))
        header_frame.pack(fill="x", padx=16, pady=(16, 0))

        title_label = ttk.Label(header_frame, text="Task Scheduling In Cloud Computing", style="Title.TLabel")
        subtitle_label = ttk.Label(header_frame, text="Advanced VM load balancing with task priorities and deadline-aware scheduling.", style="Subtitle.TLabel")
        title_label.pack(anchor="w")
        subtitle_label.pack(anchor="w", pady=(6, 0))

        control_frame = ttk.Frame(self, style="Section.TFrame", padding=(20, 14, 20, 14))
        control_frame.pack(fill="x", padx=16, pady=(10, 2))

        self._build_control_row(control_frame)

        content_frame = ttk.Frame(self, style="Section.TFrame")
        content_frame.pack(fill="both", expand=True, padx=16, pady=(2, 16))

        left_panel = ttk.Frame(content_frame, style="Section.TFrame")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_panel = ttk.Frame(content_frame, style="Section.TFrame", width=340)
        right_panel.pack(side="right", fill="y")

        self._build_vm_table(left_panel)
        self._build_task_table(left_panel)
        self._build_summary_panel(right_panel)
        self._build_project_info(right_panel)

    def _build_control_row(self, parent):
        controls = ttk.Frame(parent, style="Section.TFrame")
        controls.pack(fill="x")

        ttk.Label(controls, text="Number of tasks:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.task_count_var = tk.IntVar(value=100)
        self.task_count_spinbox = tk.Spinbox(controls, from_=10, to=500, textvariable=self.task_count_var, width=7, font=("Segoe UI", 10), bd=1, relief="solid", highlightthickness=0)
        self.task_count_spinbox.grid(row=0, column=1, padx=(10, 24), pady=2)

        ttk.Label(controls, text="Scheduler:", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w")
        self.algorithm_var = tk.StringVar(value=SUPPORTED_ALGORITHMS[0])
        self.algorithm_box = ttk.Combobox(controls, textvariable=self.algorithm_var, values=SUPPORTED_ALGORITHMS, state="readonly", width=26)
        self.algorithm_box.grid(row=0, column=3, padx=(10, 24), pady=2)

        ttk.Label(controls, text="Seed:", font=("Segoe UI", 10, "bold")).grid(row=0, column=4, sticky="w")
        self.seed_var = tk.IntVar(value=42)
        ttk.Entry(controls, textvariable=self.seed_var, width=7).grid(row=0, column=5, padx=(8, 16), pady=2)

        ttk.Label(controls, text="Live delay (ms):", font=("Segoe UI", 10, "bold")).grid(row=0, column=6, sticky="w")
        self.interval_var = tk.IntVar(value=35)
        ttk.Spinbox(controls, from_=0, to=2000, textvariable=self.interval_var, width=7).grid(row=0, column=7, padx=(8, 16), pady=2)

        self.run_button = ttk.Button(controls, text="Run Live", style="Accent.TButton", command=self.run_simulation)
        self.run_button.grid(row=0, column=8, sticky="e", padx=(0, 8))

        self.pause_button = ttk.Button(controls, text="Pause", command=self.toggle_pause, state="disabled")
        self.pause_button.grid(row=0, column=9, sticky="e", padx=(0, 8))

        self.stop_button = ttk.Button(controls, text="Stop", command=self.stop_simulation, state="disabled")
        self.stop_button.grid(row=0, column=10, sticky="e", padx=(0, 8))

        export_button = ttk.Button(controls, text="Export", style="Outline.TButton", command=self.export_results)
        export_button.grid(row=0, column=11, sticky="e", padx=(0, 8))

        self.vm_button = ttk.Button(controls, text="Configure VMs", command=self.open_vm_config)
        self.vm_button.grid(row=0, column=12, sticky="e")

        self.status_label = ttk.Label(controls, text="Ready to run scheduling.", foreground="#67e8f9", font=("Segoe UI", 10, "italic"))
        self.status_label.grid(row=1, column=0, columnspan=9, sticky="w", pady=(10, 0))

        self.progress = ttk.Progressbar(controls, mode="determinate", length=240)
        self.progress.grid(row=1, column=9, columnspan=4, sticky="e", pady=(10, 0))

        controls.grid_columnconfigure(3, weight=1)

    def _build_vm_table(self, parent):
        vm_frame = ttk.Labelframe(parent, text="VM Scheduling Results", style="Card.TLabelframe", padding=14)
        vm_frame.pack(fill="both", expand=True)

        vm_columns = ("VM ID", "MIPS", "Tasks", "Total Length", "Avg Length", "Load", "ETA")
        self.vm_table = ttk.Treeview(vm_frame, columns=vm_columns, show="headings", height=12)

        for col in vm_columns:
            self.vm_table.heading(col, text=col)
            self.vm_table.column(col, width=100, anchor="center")
        self.vm_table.column("VM ID", width=90)
        self.vm_table.column("Total Length", width=110)
        self.vm_table.column("Avg Length", width=110)

        self.vm_table.pack(fill="both", expand=True)

    def _build_task_table(self, parent):
        task_frame = ttk.Labelframe(parent, text="Top Task Details", style="Card.TLabelframe", padding=14)
        task_frame.pack(fill="both", expand=True, pady=(12, 0))

        task_columns = ("Task ID", "Length", "Priority", "Deadline", "Description")
        self.task_table = ttk.Treeview(task_frame, columns=task_columns, show="headings", height=10)

        for col in task_columns:
            self.task_table.heading(col, text=col)
            self.task_table.column(col, width=110, anchor="center")
        self.task_table.column("Description", width=180, anchor="w")

        self.task_table.pack(fill="both", expand=True)

    def _build_summary_panel(self, parent):
        summary_frame = ttk.Labelframe(parent, text="Run Summary", style="Card.TLabelframe", padding=16)
        summary_frame.pack(fill="x", pady=(0, 12))

        self.summary_rows = {}
        labels = ["Scheduler", "Tasks", "Completed", "Total Length", "Makespan", "Deadline Rate", "Estimated Cost"]
        for index, label in enumerate(labels):
            ttk.Label(summary_frame, text=f"{label}:", font=("Segoe UI", 10, "bold"), foreground="#93c5fd").grid(row=index, column=0, sticky="w", pady=6)
            value = ttk.Label(summary_frame, text="—", foreground="#e2e8f0")
            value.grid(row=index, column=1, sticky="w", padx=(12, 0), pady=6)
            self.summary_rows[label] = value

    def _build_project_info(self, parent):
        info_frame = ttk.Labelframe(parent, text="Project Info", style="Card.TLabelframe", padding=16)
        info_frame.pack(fill="both", expand=True)

        info_text = (
            "This advanced simulation assigns compute tasks to cloud VMs using different scheduling strategies.\n\n"
            "- Balanced scheduler minimizes load variance.\n"
            "- Priority scheduler sorts urgent tasks first.\n"
            "- Deadline scheduler respects task due dates.\n\n"
            "Results are saved to output/task_vm_mapping.xlsx with allocation metadata."
        )
        ttk.Label(info_frame, text=info_text, wraplength=300, justify="left", font=("Segoe UI", 10), foreground="#cbd5e1").pack(fill="both", expand=True)

    def _read_vms(self):
        vms = []
        if not self.vm_entries:
            defaults = [
                ("VM1", 400, 512),
                ("VM2", 520, 768),
                ("VM3", 680, 1024),
                ("VM4", 820, 1536),
                ("VM5", 980, 2048),
            ]
            for vm_id, mips, ram in defaults:
                vms.append(VirtualMachine(vm_id, mips, ram))
            return vms

        for vm_entry in self.vm_entries:
            mips = vm_entry["mips_var"].get()
            ram = vm_entry["ram_var"].get()
            if mips <= 0 or ram <= 0:
                messagebox.showerror("Validation Error", "VM MIPS and RAM must be positive integers.")
                return None
            vms.append(VirtualMachine(vm_entry["vm_id"], mips, ram))
        return vms

    def open_vm_config(self):
        dialog = tk.Toplevel(self)
        dialog.title("Configure Virtual Machines")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg="#111a2b")

        ttk.Label(dialog, text="Define the compute capacity used by this run.", style="Subtitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", padx=18, pady=(16, 10)
        )
        headers = ("VM ID", "MIPS", "RAM (MB)")
        for column, header in enumerate(headers):
            ttk.Label(dialog, text=header, font=("Segoe UI", 10, "bold")).grid(row=1, column=column, padx=8, pady=6)

        defaults = [("VM1", 400, 512), ("VM2", 520, 768), ("VM3", 680, 1024)]
        existing = [(entry["vm_id"], entry["mips_var"].get(), entry["ram_var"].get()) for entry in self.vm_entries]
        rows = existing or defaults
        fields = []
        for row_index, values in enumerate(rows, start=2):
            row_fields = []
            for column, value in enumerate(values):
                variable = tk.StringVar(value=str(value))
                ttk.Entry(dialog, textvariable=variable, width=15).grid(row=row_index, column=column, padx=8, pady=4)
                row_fields.append(variable)
            fields.append(row_fields)

        def save_vms():
            try:
                configured = []
                seen_ids = set()
                for vm_id_var, mips_var, ram_var in fields:
                    vm_id = vm_id_var.get().strip()
                    mips = int(mips_var.get())
                    ram = int(ram_var.get())
                    if not vm_id or vm_id in seen_ids or mips <= 0 or ram <= 0:
                        raise ValueError("VM IDs must be unique, and MIPS/RAM must be positive.")
                    seen_ids.add(vm_id)
                    configured.append({"vm_id": vm_id, "mips_var": tk.IntVar(value=mips), "ram_var": tk.IntVar(value=ram)})
                self.vm_entries = configured
                self._update_status(f"{len(configured)} virtual machines configured.", True)
                dialog.destroy()
            except ValueError as exc:
                messagebox.showerror("VM Configuration", str(exc), parent=dialog)

        ttk.Button(dialog, text="Save Configuration", style="Accent.TButton", command=save_vms).grid(
            row=len(fields) + 2, column=0, columnspan=2, padx=8, pady=(14, 18), sticky="ew"
        )
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(
            row=len(fields) + 2, column=2, columnspan=2, padx=8, pady=(14, 18), sticky="ew"
        )

    def run_simulation(self):
        try:
            vms = self._read_vms()
            if vms is None:
                return

            task_count = self.task_count_var.get()
            if task_count < 1:
                messagebox.showerror("Validation Error", "Task count must be at least 1.")
                return

            if self.worker_thread and self.worker_thread.is_alive():
                return

            tasks = generate_tasks(task_count, seed=self.seed_var.get())
            algorithm = self.algorithm_var.get()
            self.tasks = tasks
            self.vms = vms
            self.mapping = []
            self.run_token += 1
            run_token = self.run_token
            interval_ms = max(0, self.interval_var.get())
            self._clear_tables()
            self.progress.configure(maximum=task_count, value=0)
            self.stop_event.clear()
            self.pause_event.set()
            self.run_button.configure(state="disabled")
            self.pause_button.configure(state="normal", text="Pause")
            self.stop_button.configure(state="normal")
            self._update_status("Live scheduling is running...", success=True)
            self.worker_thread = threading.Thread(target=self._schedule_worker, args=(tasks, vms, algorithm, interval_ms, run_token), daemon=True)
            self.worker_thread.start()
            self.after(50, self._process_events)

        except Exception as exc:
            messagebox.showerror("Simulation Error", str(exc))
            self._update_status("✖ Simulation failed.", success=False)

    def _schedule_worker(self, tasks, vms, algorithm, interval_ms, run_token):
        try:
            for mapping_row in schedule_tasks_stream(tasks, vms, algorithm):
                if self.stop_event.is_set():
                    self.events.put(("stopped", run_token))
                    return
                self.pause_event.wait()
                self.events.put(("row", (run_token, mapping_row)))
                time.sleep(interval_ms / 1000)
            self.events.put(("done", (run_token, algorithm, vms)))
        except Exception as exc:
            self.events.put(("error", (run_token, exc)))

    def _process_events(self):
        try:
            while True:
                event_type, payload = self.events.get_nowait()
                if event_type == "row":
                    event_token, mapping_row = payload
                    if event_token != self.run_token:
                        continue
                    self.mapping.append(mapping_row)
                    self.progress.configure(value=len(self.mapping))
                    self._populate_vm_table(self.vms)
                    self._populate_task_table(self.mapping)
                    self._update_live_summary(mapping_row)
                elif event_type == "done":
                    event_token, algorithm, vms = payload
                    if event_token != self.run_token:
                        continue
                    metrics = calculate_metrics(self.mapping, vms)
                    vm_rows = self._vm_rows(vms)
                    save_to_excel(self.mapping, metrics=metrics, vm_rows=vm_rows)
                    self._update_summary(algorithm, self.tasks, vms, metrics)
                    self._finish_run("Scheduling completed. Live results saved to output/task_vm_mapping.xlsx", True)
                elif event_type == "stopped":
                    if payload == self.run_token:
                        self._finish_run("Scheduling stopped by user.", False)
                elif event_type == "error":
                    event_token, error = payload
                    if event_token == self.run_token:
                        raise error
        except queue.Empty:
            pass
        except Exception as exc:
            messagebox.showerror("Simulation Error", str(exc))
            self._finish_run("Simulation failed.", False)
            return
        if self.worker_thread and self.worker_thread.is_alive():
            self.after(50, self._process_events)

    def toggle_pause(self):
        if not self.worker_thread or not self.worker_thread.is_alive():
            return
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.configure(text="Resume")
            self._update_status("Scheduling paused.", True)
        else:
            self.pause_event.set()
            self.pause_button.configure(text="Pause")
            self._update_status("Scheduling resumed.", True)

    def stop_simulation(self):
        if not self.worker_thread or not self.worker_thread.is_alive():
            return
        self.stop_event.set()
        self.pause_event.set()
        self._update_status("Stopping scheduling...", success=True)

    def _finish_run(self, message, success):
        self.run_button.configure(state="normal")
        self.pause_button.configure(state="disabled", text="Pause")
        self.stop_button.configure(state="disabled")
        self._update_status(message, success)

    def _clear_tables(self):
        self.vm_table.delete(*self.vm_table.get_children())
        self.task_table.delete(*self.task_table.get_children())

    def _vm_rows(self, vms):
        makespan = max((vm.estimated_finish_time() for vm in vms), default=0)
        return [{
            "vm_id": vm.vm_id,
            "mips": vm.mips,
            "ram": vm.ram,
            "tasks": vm.total_tasks(),
            "total_length": vm.total_load(),
            "finish_time": round(vm.estimated_finish_time(), 3),
            "utilization_percent": round(vm.utilization(makespan), 2),
            "estimated_cost": round(vm.estimated_cost(), 5)
        } for vm in vms]

    def _populate_vm_table(self, vms):
        self.vm_table.delete(*self.vm_table.get_children())
        for vm in vms:
            avg_length = vm.total_load() / vm.total_tasks() if vm.total_tasks() else 0
            self.vm_table.insert(
                "",
                "end",
                values=(
                    vm.vm_id,
                    vm.mips,
                    vm.total_tasks(),
                    vm.total_load(),
                    f"{avg_length:.2f}",
                    f"{vm.total_load():.2f}",
                    f"{vm.estimated_finish_time():.2f}"
                )
            )

    def _populate_task_table(self, mapping):
        self.task_table.delete(*self.task_table.get_children())
        top_tasks = sorted(mapping, key=lambda item: (-item["priority"], item["deadline"]))[:10]
        for item in top_tasks:
            self.task_table.insert(
                "",
                "end",
                values=(
                    item["task_id"],
                    item["task_length"],
                    item["priority"],
                    item["deadline"],
                    item["description"]
                )
            )

    def _update_live_summary(self, latest):
        self.summary_rows["Completed"].config(text=f"{len(self.mapping)} / {len(self.tasks)}")
        self.summary_rows["Makespan"].config(text=f"{latest['completion_time']:.2f}s")
        self.summary_rows["Deadline Rate"].config(text=f"{sum(item['deadline_met'] for item in self.mapping) / len(self.mapping) * 100:.1f}%")

    def _update_summary(self, algorithm, tasks, vms, metrics=None):
        metrics = metrics or calculate_metrics(self.mapping, vms)
        total_length = sum(task["length"] for task in tasks)
        max_vm_tasks = max((vm.total_tasks() for vm in vms), default=0)
        peak_load = max((vm.total_load() for vm in vms), default=0)

        self.summary_rows["Scheduler"].config(text=algorithm)
        self.summary_rows["Tasks"].config(text=str(len(tasks)))
        self.summary_rows["Completed"].config(text=str(len(self.mapping)))
        self.summary_rows["Total Length"].config(text=str(total_length))
        self.summary_rows["Makespan"].config(text=f"{metrics['makespan']:.2f}s")
        self.summary_rows["Deadline Rate"].config(text=f"{metrics['deadline_rate']:.1f}%")
        self.summary_rows["Estimated Cost"].config(text=f"${metrics['estimated_cost']:.4f}")

    def export_results(self):
        if not self.mapping:
            messagebox.showinfo("Export", "Run a simulation first before exporting results.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
            initialfile="task_vm_mapping.xlsx"
        )
        if file_path:
            metrics = calculate_metrics(self.mapping, self.vms)
            save_to_excel(self.mapping, file_path, metrics, self._vm_rows(self.vms))
            messagebox.showinfo("Export Complete", f"Results saved to {file_path}")
            self._update_status(f"✔ Exported to {file_path}", success=True)

    def clear_results(self):
        was_running = self.worker_thread and self.worker_thread.is_alive()
        self.stop_simulation()
        if was_running:
            self.run_token += 1
            self._finish_run("Results cleared. Finishing active worker...", True)
        self._clear_tables()
        self.mapping = []
        for label in self.summary_rows.values():
            label.config(text="—")
        self._update_status("Results cleared.", success=True)

    def _update_status(self, message, success=True):
        self.status_label.config(text=message, foreground="#34d399" if success else "#fb7185")


if __name__ == "__main__":
    app = SchedulerApp()
    app.mainloop()
