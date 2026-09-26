import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from datacenter import VirtualMachine
from excel_writer import save_to_excel
from scheduler import SUPPORTED_ALGORITHMS, calculate_metrics, schedule_tasks
from task_generator import generate_tasks
from .database import get_connection


class Dashboard(tk.Frame):
    def __init__(self, root, user):
        super().__init__(root, bg='#0b1220')
        self.root, self.user = root, user
        self.mapping, self.vms, self.tasks = [], [], []
        self.pack(fill='both', expand=True)
        self._style()
        self._build_shell()
        self.show_page('Dashboard')

    def _style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TButton', font=('Segoe UI', 10), padding=7, background='#1a2b42', foreground='#d8e3f0', borderwidth=0)
        style.map('TButton', background=[('active', '#294566')], foreground=[('active', '#ffffff')])
        style.configure('Primary.TButton', background='#1677ff', foreground='white', padding=8)
        style.map('Primary.TButton', background=[('active', '#3b91ff')])
        style.configure('Treeview', rowheight=32, font=('Segoe UI', 10), background='#111c2e', fieldbackground='#111c2e', foreground='#d8e3f0', borderwidth=0)
        style.map('Treeview', background=[('selected', '#164e7a')], foreground=[('selected', '#ffffff')])
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background='#1b304a', foreground='#9fc2e5', relief='flat')
        style.configure('TEntry', fieldbackground='#0d1727', foreground='#edf5ff', insertcolor='#ffffff', bordercolor='#29425e', padding=7)
        style.configure('TCombobox', fieldbackground='#0d1727', foreground='#edf5ff', selectbackground='#164e7a', selectforeground='#ffffff', padding=7)

    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg='#102a43', width=220)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        self._sidebar_logo()
        self.nav_buttons = {}
        for name in ('Dashboard', 'Users', 'Tasks', 'Virtual Machines', 'Scheduling', 'Results', 'Algorithm Comparison'):
            button = tk.Button(self.sidebar, text='  ' + name, anchor='w', relief='flat', bd=0, bg='#102a43', fg='#c9d8e8', activebackground='#1d4f73', activeforeground='white', font=('Segoe UI', 10), padx=18, pady=10, command=lambda item=name: self.show_page(item))
            button.pack(fill='x')
            self.nav_buttons[name] = button
        tk.Frame(self.sidebar, bg='#31516b', height=1).pack(fill='x', padx=18, pady=18)
        tk.Button(self.sidebar, text='  Logout', anchor='w', relief='flat', bd=0, bg='#102a43', fg='#fca5a5', activebackground='#7f1d1d', activeforeground='white', font=('Segoe UI', 10), padx=18, pady=10, command=self.logout).pack(fill='x')
        self.content = tk.Frame(self, bg='#0b1220')
        self.content.pack(side='left', fill='both', expand=True)

    def _sidebar_logo(self):
        holder = tk.Frame(self.sidebar, bg='#102a43')
        holder.pack(anchor='w', padx=22, pady=(24, 10))
        mark = tk.Canvas(holder, width=42, height=42, bg='#102a43', highlightthickness=0)
        mark.pack(side='left')
        mark.create_oval(4, 4, 38, 38, fill='#12355a', outline='#36b5e8', width=2)
        mark.create_rectangle(14, 14, 28, 30, fill='#1677ff', outline='')
        mark.create_line(10, 34, 32, 34, fill='#52d6ff', width=2)
        tk.Label(holder, text='CLOUD TASK\nSCHEDULING', bg='#102a43', fg='white', font=('Segoe UI', 10, 'bold'), justify='left').pack(side='left', padx=(9, 0))
        tk.Label(self.sidebar, text='CLOUD COMPUTING CONTROL', bg='#102a43', fg='#70c7f5', font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=25, pady=(0, 28))

    def show_page(self, page):
        for name, button in self.nav_buttons.items():
            button.configure(bg='#1d4f73' if name == page else '#102a43', fg='white' if name == page else '#c9d8e8')
        for child in self.content.winfo_children():
            child.destroy()
        builders = {'Dashboard': self.dashboard_page, 'Users': self.users_page, 'Tasks': self.tasks_page, 'Virtual Machines': self.vms_page, 'Scheduling': self.scheduling_page, 'Results': self.results_page, 'Algorithm Comparison': self.comparison_page}
        builders[page]()

    def _header(self, title, subtitle=''):
        top = tk.Frame(self.content, bg='#111c2e', padx=28, pady=22, highlightbackground='#1e3550', highlightthickness=1)
        top.pack(fill='x')
        tk.Label(top, text=title, bg='#111c2e', fg='#f5f9ff', font=('Segoe UI', 21, 'bold')).pack(anchor='w')
        if subtitle:
            tk.Label(top, text=subtitle, bg='#111c2e', fg='#8ca3bd', font=('Segoe UI', 10)).pack(anchor='w', pady=(5, 0))
        tk.Label(top, text=f"●  {self.user['username']}  |  {self.user['role']}", bg='#111c2e', fg='#52b7ff', font=('Segoe UI', 10)).place(relx=1, x=-28, y=8, anchor='ne')

    def _body(self):
        body = tk.Frame(self.content, bg='#0b1220', padx=28, pady=24)
        body.pack(fill='both', expand=True)
        return body

    def _table(self, parent, columns, rows):
        frame = tk.Frame(parent, bg='#111c2e', highlightbackground='#1e3550', highlightthickness=1)
        frame.pack(fill='both', expand=True)
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor='center', width=max(100, 760 // len(columns)))
        scroll = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        for row in rows:
            tree.insert('', 'end', values=row)
        return tree

    def _stat(self, parent, label, value, color):
        card = tk.Frame(parent, bg='#111c2e', padx=18, pady=14, highlightbackground='#1e3550', highlightthickness=1)
        card.pack(side='left', fill='x', expand=True, padx=(0, 12))
        tk.Label(card, text=label.upper(), bg='#111c2e', fg='#8ca3bd', font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        tk.Label(card, text=value, bg='#111c2e', fg=color, font=('Segoe UI', 22, 'bold')).pack(anchor='w', pady=(5, 0))

    def dashboard_page(self):
        self._header('Dashboard', 'Monitor your cloud workload and scheduling performance.')
        body = self._body()
        with get_connection() as conn:
            users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            tasks = conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
            vms = conn.execute('SELECT COUNT(*) FROM virtual_machines').fetchone()[0]
            runs = conn.execute('SELECT COUNT(*) FROM scheduling_results').fetchone()[0]
        stats = tk.Frame(body, bg='#0b1220')
        stats.pack(fill='x', pady=(0, 24))
        for label, value, color in [('Total Users', users, '#2563eb'), ('Total Tasks', tasks, '#0f766e'), ('Virtual Machines', vms, '#7c3aed'), ('Completed Runs', runs, '#16a34a')]:
            self._stat(stats, label, value, color)
        chart_area = tk.Frame(body, bg='#0b1220')
        chart_area.pack(fill='x', pady=(0, 24))
        with get_connection() as conn:
            status_rows = conn.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status').fetchall()
            run_rows = conn.execute('SELECT algorithm, makespan FROM scheduling_results ORDER BY id DESC LIMIT 6').fetchall()
        figure = Figure(figsize=(9.6, 2.9), dpi=100, facecolor='#0b1220')
        status_axis = figure.add_subplot(121)
        run_axis = figure.add_subplot(122)
        status_labels = [row[0] for row in status_rows] or ['No tasks']
        status_values = [row[1] for row in status_rows] or [1]
        status_axis.set_facecolor('#111c2e'); run_axis.set_facecolor('#111c2e')
        status_axis.pie(status_values, labels=status_labels, autopct='%1.0f%%', colors=('#2f80ed', '#22c55e', '#f59e0b', '#ef4444'), textprops={'fontsize': 8, 'color': '#d8e3f0'})
        status_axis.set_title('TASK STATUS', fontsize=10, color='#c8d9ec', pad=8)
        if run_rows:
            labels = [str(row[0]).replace(' Scheduler', '') for row in reversed(run_rows)]
            values = [row[1] for row in reversed(run_rows)]
            run_axis.barh(labels, values, color='#36b5e8')
            run_axis.set_xlabel('Makespan', fontsize=8, color='#8ca3bd')
        else:
            run_axis.text(0.5, 0.5, 'Run a schedule to see trends', ha='center', va='center', color='#8ca3bd')
        run_axis.set_title('RECENT MAKESPAN', fontsize=10, color='#c8d9ec', pad=8)
        run_axis.tick_params(labelsize=8, colors='#8ca3bd')
        for axis in (status_axis, run_axis):
            for spine in axis.spines.values(): spine.set_color('#1e3550')
        figure.tight_layout(pad=2)
        canvas = FigureCanvasTkAgg(figure, master=chart_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='x')
        tk.Label(body, text='System Overview', bg='#0b1220', fg='#f5f9ff', font=('Segoe UI', 15, 'bold')).pack(anchor='w', pady=(0, 10))
        with get_connection() as conn:
            rows = conn.execute('SELECT algorithm, total_tasks, completed, makespan, created_at FROM scheduling_results ORDER BY id DESC LIMIT 8').fetchall()
        self._table(body, ('Algorithm', 'Tasks', 'Completed', 'Makespan', 'Created'), [tuple(row) for row in rows] or [('No runs yet', '-', '-', '-', '-')])

    def users_page(self):
        self._header('Users Management', 'Manage accounts that can access the scheduler.')
        body = self._body()
        toolbar = tk.Frame(body, bg='#0b1220')
        toolbar.pack(fill='x', pady=(0, 14))
        ttk.Button(toolbar, text='Add User', style='Primary.TButton', command=self.add_user).pack(side='right')
        with get_connection() as conn:
            rows = conn.execute('SELECT id, username, email, role, status FROM users ORDER BY id').fetchall()
        self._table(body, ('ID', 'Username', 'Email', 'Role', 'Status'), [tuple(row) for row in rows])

    def add_user(self):
        dialog = tk.Toplevel(self)
        dialog.title('Add User')
        dialog.transient(self.root)
        dialog.grab_set()
        form = tk.Frame(dialog, padx=24, pady=22)
        form.pack()
        fields = {}
        for row, label in enumerate(('Username', 'Email', 'Role', 'Password')):
            tk.Label(form, text=label).grid(row=row, column=0, sticky='w', pady=6)
            entry = ttk.Entry(form, width=30, show='*' if label == 'Password' else '')
            entry.grid(row=row, column=1, padx=(15, 0), pady=6)
            fields[label] = entry

        def save():
            try:
                with get_connection() as conn:
                    conn.execute('INSERT INTO users (username,email,role,password) VALUES (?,?,?,?)', (fields['Username'].get().strip(), fields['Email'].get().strip(), fields['Role'].get().strip() or 'User', fields['Password'].get() or 'password'))
                    conn.commit()
                dialog.destroy()
                self.show_page('Users')
            except Exception as exc:
                messagebox.showerror('User', str(exc), parent=dialog)

        ttk.Button(form, text='Save User', style='Primary.TButton', command=save).grid(row=4, column=0, columnspan=2, sticky='ew', pady=(12, 0))

    def tasks_page(self):
        self._header('Task Submission', 'Create and track compute tasks awaiting execution.')
        body = self._body()
        form = tk.Frame(body, bg='#111c2e', padx=16, pady=14, highlightbackground='#1e3550', highlightthickness=1)
        form.pack(fill='x', pady=(0, 16))
        name, owner = ttk.Entry(form, width=24), ttk.Entry(form, width=18)
        priority = ttk.Combobox(form, values=('Low', 'Medium', 'High'), state='readonly', width=12)
        priority.set('Medium')
        for widget, label in ((name, 'Task name'), (owner, 'Owner'), (priority, 'Priority')):
            tk.Label(form, text=label, bg='#111c2e', fg='#9fb5cc').pack(side='left', padx=(0, 6))
            widget.pack(side='left', padx=(0, 16))

        def submit():
            if not name.get().strip():
                return messagebox.showwarning('Task', 'Enter a task name.')
            with get_connection() as conn:
                conn.execute('INSERT INTO tasks (task_name, owner, priority, status) VALUES (?,?,?,?)', (name.get().strip(), owner.get().strip() or self.user['username'], priority.get(), 'Queued'))
                conn.commit()
            self.show_page('Tasks')

        ttk.Button(form, text='Submit Task', style='Primary.TButton', command=submit).pack(side='left')
        with get_connection() as conn:
            rows = conn.execute('SELECT id, task_name, owner, priority, status, created_at FROM tasks ORDER BY id DESC').fetchall()
        self._table(body, ('ID', 'Task Name', 'Owner', 'Priority', 'Status', 'Created'), [tuple(row) for row in rows] or [('-', 'No tasks submitted', '-', '-', '-', '-')])

    def vms_page(self):
        self._header('Virtual Machines', 'Review compute capacity available to the scheduler.')
        body = self._body()
        toolbar = tk.Frame(body, bg='#0b1220')
        toolbar.pack(fill='x', pady=(0, 14))
        ttk.Button(toolbar, text='+ Add Virtual Machine', style='Primary.TButton', command=self.add_vm).pack(side='right')
        with get_connection() as conn:
            rows = conn.execute('SELECT id, name, mips, ram, status FROM virtual_machines').fetchall()
        self._table(body, ('VM ID', 'Name', 'MIPS', 'RAM (MB)', 'Status'), [tuple(row) for row in rows])

    def add_vm(self):
        dialog = tk.Toplevel(self)
        dialog.title('Add Virtual Machine')
        dialog.configure(bg='#111c2e')
        dialog.transient(self.root)
        dialog.grab_set()
        form = tk.Frame(dialog, bg='#111c2e', padx=24, pady=22)
        form.pack()
        fields = {}
        for row, label in enumerate(('VM name', 'MIPS', 'RAM (MB)')):
            tk.Label(form, text=label, bg='#111c2e', fg='#d8e3f0').grid(row=row, column=0, sticky='w', pady=6)
            entry = ttk.Entry(form, width=28)
            entry.grid(row=row, column=1, padx=(18, 0), pady=6)
            fields[label] = entry

        def save():
            try:
                name, mips, ram = fields['VM name'].get().strip(), int(fields['MIPS'].get()), int(fields['RAM (MB)'].get())
                if not name or mips <= 0 or ram <= 0:
                    raise ValueError
                with get_connection() as conn:
                    conn.execute('INSERT INTO virtual_machines (name, mips, ram, status) VALUES (?, ?, ?, ?)', (name, mips, ram, 'Idle'))
                    conn.commit()
                dialog.destroy()
                self.show_page('Virtual Machines')
            except ValueError:
                messagebox.showerror('Virtual Machine', 'Enter a name and positive numeric capacity values.', parent=dialog)

        ttk.Button(form, text='Save Virtual Machine', style='Primary.TButton', command=save).grid(row=3, column=0, columnspan=2, sticky='ew', pady=(14, 0))

    def _load_vms(self):
        with get_connection() as conn:
            rows = conn.execute('SELECT id, name, mips, ram FROM virtual_machines').fetchall()
        return [VirtualMachine(f'VM{row[0]}', row[2], row[3]) for row in rows]

    def scheduling_page(self):
        self._header('Scheduling', 'Select an algorithm and allocate queued work across your virtual machines.')
        body = self._body()
        controls = tk.Frame(body, bg='#111c2e', padx=16, pady=14, highlightbackground='#1e3550', highlightthickness=1)
        controls.pack(fill='x', pady=(0, 16))
        algorithm = ttk.Combobox(controls, values=SUPPORTED_ALGORITHMS, state='readonly', width=28)
        algorithm.set(SUPPORTED_ALGORITHMS[0])
        algorithm.pack(side='left', padx=(0, 12))
        ttk.Button(controls, text='Run Scheduler', style='Primary.TButton', command=lambda: self.run_schedule(algorithm.get())).pack(side='left')
        self.schedule_table = self._table(body, ('Task ID', 'Task', 'VM', 'Start', 'Completion', 'Deadline'), [])

    def run_schedule(self, algorithm):
        with get_connection() as conn:
            db_tasks = conn.execute('SELECT id, task_name, priority FROM tasks WHERE status != "Completed"').fetchall()
        if not db_tasks:
            db_tasks = [{'id': i + 1, 'task_name': task['description'], 'priority': task['priority']} for i, task in enumerate(generate_tasks(8, seed=42))]
        tasks = [{'task_id': f'T{row["id"]}', 'length': 100 + (int(row['id']) * 83) % 900, 'priority': {'High': 5, 'Medium': 3, 'Low': 1}.get(row['priority'], row['priority'] if isinstance(row['priority'], int) else 3), 'deadline': 1800, 'description': row['task_name']} for row in db_tasks]
        self.vms = self._load_vms()
        self.mapping = schedule_tasks(tasks, self.vms, algorithm)
        self.tasks = tasks
        metrics = calculate_metrics(self.mapping, self.vms)
        with get_connection() as conn:
            conn.execute('INSERT INTO scheduling_results (algorithm,total_tasks,completed,makespan) VALUES (?,?,?,?)', (algorithm, len(tasks), len(self.mapping), metrics['makespan']))
            conn.execute('UPDATE tasks SET status="Completed" WHERE status != "Completed"')
            conn.commit()
        self.schedule_table.delete(*self.schedule_table.get_children())
        for item in self.mapping:
            self.schedule_table.insert('', 'end', values=(item['task_id'], item['description'], item['vm_id'], item['start_time'], item['completion_time'], 'Met' if item['deadline_met'] else 'Missed'))
        messagebox.showinfo('Scheduling', f'{len(self.mapping)} tasks scheduled with {algorithm}.')

    def results_page(self):
        self._header('Results', 'Inspect the latest allocation metrics and export them to Excel.')
        body = self._body()
        toolbar = tk.Frame(body, bg='#0b1220')
        toolbar.pack(fill='x', pady=(0, 14))
        ttk.Button(toolbar, text='Export Excel', style='Primary.TButton', command=self.export_results).pack(side='right')
        with get_connection() as conn:
            task_total = conn.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
            completed = conn.execute('SELECT COUNT(*) FROM tasks WHERE status = "Completed"').fetchone()[0]
            latest = conn.execute('SELECT makespan FROM scheduling_results ORDER BY id DESC LIMIT 1').fetchone()
        summary = tk.Frame(body, bg='#0b1220')
        summary.pack(fill='x', pady=(0, 18))
        for label, value, color in [('Total Tasks', task_total, '#52b7ff'), ('Completed', completed, '#34d399'), ('Completion Rate', f'{completed / task_total * 100:.0f}%' if task_total else '0%', '#fbbf24'), ('Latest Makespan', f'{latest[0]:.2f}' if latest else '-', '#c084fc')]:
            self._stat(summary, label, value, color)
        with get_connection() as conn:
            rows = conn.execute('SELECT algorithm,total_tasks,completed,makespan,created_at FROM scheduling_results ORDER BY id DESC').fetchall()
        self._table(body, ('Algorithm', 'Tasks', 'Completed', 'Makespan', 'Created'), [tuple(row) for row in rows] or [('No results', '-', '-', '-', '-')])

    def export_results(self):
        if not self.mapping:
            return messagebox.showinfo('Export', 'Run a schedule first.')
        path = filedialog.asksaveasfilename(defaultextension='.xlsx', initialfile='task_vm_mapping.xlsx', filetypes=[('Excel Workbook', '*.xlsx')])
        if path:
            save_to_excel(self.mapping, path, calculate_metrics(self.mapping, self.vms))
            messagebox.showinfo('Export', 'Results exported successfully.')

    def comparison_page(self):
        self._header('Algorithm Comparison', 'Compare scheduling strategies on the current workload.')
        body = self._body()
        ttk.Button(body, text='Compare All Algorithms', style='Primary.TButton', command=self.compare_algorithms).pack(anchor='e', pady=(0, 14))
        chart_frame = tk.Frame(body, bg='#111c2e', highlightbackground='#1e3550', highlightthickness=1)
        chart_frame.pack(fill='x', pady=(0, 16))
        self.comparison_figure = Figure(figsize=(9.6, 2.8), dpi=100, facecolor='#111c2e')
        self.comparison_axis = self.comparison_figure.add_subplot(111)
        self.comparison_axis.set_facecolor('#111c2e')
        self.comparison_canvas = FigureCanvasTkAgg(self.comparison_figure, master=chart_frame)
        self.comparison_canvas.draw()
        self.comparison_canvas.get_tk_widget().pack(fill='x')
        self.comparison_table = self._table(body, ('Algorithm', 'Makespan', 'Throughput', 'Deadline Rate', 'Estimated Cost'), [])

    def compare_algorithms(self):
        tasks = generate_tasks(12, seed=42)
        rows = []
        for algorithm in SUPPORTED_ALGORITHMS:
            vms = self._load_vms()
            mapping = schedule_tasks(tasks, vms, algorithm)
            metrics = calculate_metrics(mapping, vms)
            rows.append((algorithm, metrics['makespan'], metrics['throughput'], f"{metrics['deadline_rate']}%", f"${metrics['estimated_cost']:.4f}"))
        self.comparison_table.delete(*self.comparison_table.get_children())
        for row in rows:
            self.comparison_table.insert('', 'end', values=row)
        self.comparison_axis.clear()
        labels = [row[0].replace(' Scheduler', '') for row in rows]
        values = [row[1] for row in rows]
        self.comparison_axis.set_facecolor('#111c2e')
        self.comparison_axis.bar(labels, values, color=('#36b5e8', '#4ade80', '#fbbf24', '#c084fc', '#fb7185', '#60a5fa'))
        self.comparison_axis.set_title('MAKESPAN COMPARISON', color='#d8e3f0', fontsize=10)
        self.comparison_axis.tick_params(axis='x', labelrotation=20, labelsize=8, colors='#9fb5cc')
        self.comparison_axis.tick_params(axis='y', labelsize=8, colors='#9fb5cc')
        for spine in self.comparison_axis.spines.values(): spine.set_color('#29425e')
        self.comparison_figure.tight_layout(pad=2)
        self.comparison_canvas.draw()

    def logout(self):
        self.destroy()
        self.root.show_login()
