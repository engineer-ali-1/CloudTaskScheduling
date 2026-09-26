import tkinter as tk
from tkinter import ttk

from .database import get_connection, init_db


class LoginWindow(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.title('Cloud Task Scheduling in Cloud Computing')
        init_db()
        self.geometry('500x590')
        self.configure(bg='#0b1220')
        self.resizable(False, False)
        self._style()
        self._show_login()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Auth.TFrame', background='#111c2e')
        style.configure('Auth.TLabel', background='#111c2e', foreground='#d8e3f0', font=('Segoe UI', 10))
        style.configure('AuthTitle.TLabel', background='#111c2e', foreground='#f5f9ff', font=('Segoe UI', 22, 'bold'))
        style.configure('AuthMuted.TLabel', background='#111c2e', foreground='#8ca3bd', font=('Segoe UI', 9))
        style.configure('AuthPrimary.TButton', background='#1677ff', foreground='white', font=('Segoe UI', 10, 'bold'), padding=10)
        style.map('AuthPrimary.TButton', background=[('active', '#3b91ff')])
        style.configure('Auth.TEntry', fieldbackground='#0d1727', foreground='#edf5ff', insertcolor='#ffffff', bordercolor='#29425e', padding=8)
        style.map('Auth.TEntry', fieldbackground=[('focus', '#12233b')], bordercolor=[('focus', '#1677ff')])

    def _card(self, title, subtitle):
        for child in self.winfo_children():
            child.destroy()
        shell = tk.Frame(self, bg='#0b1220', padx=34, pady=30)
        shell.pack(fill='both', expand=True)
        self._logo(shell, compact=True)
        card = ttk.Frame(shell, style='Auth.TFrame', padding=28)
        card.pack(fill='both', expand=True)
        ttk.Label(card, text='Cloud Task Scheduling in Cloud Computing', style='AuthMuted.TLabel', wraplength=380).pack(anchor='w', pady=(0, 12))
        ttk.Label(card, text=title, style='AuthTitle.TLabel').pack(anchor='w')
        ttk.Label(card, text=subtitle, style='AuthMuted.TLabel', wraplength=380).pack(anchor='w', pady=(7, 24))
        return card

    def _logo(self, parent, compact=False):
        holder = tk.Frame(parent, bg=parent.cget('bg'))
        holder.pack(anchor='w', pady=(0, 14))
        size = 42 if compact else 54
        mark = tk.Canvas(holder, width=size, height=size, bg=parent.cget('bg'), highlightthickness=0)
        mark.pack(side='left')
        mark.create_oval(5, 5, size - 5, size - 5, fill='#12355a', outline='#36b5e8', width=2)
        mark.create_rectangle(size * .32, size * .38, size * .68, size * .72, fill='#1677ff', outline='')
        mark.create_line(size * .24, size * .82, size * .76, size * .82, fill='#52d6ff', width=2)
        tk.Label(holder, text='CLOUD TASK\nSCHEDULING', bg=parent.cget('bg'), fg='#d8e3f0', font=('Segoe UI', 9, 'bold'), justify='left').pack(side='left', padx=(10, 0))

    def _field(self, parent, label, show=None):
        ttk.Label(parent, text=label, style='Auth.TLabel').pack(anchor='w', pady=(8, 5))
        entry = ttk.Entry(parent, show=show or '', style='Auth.TEntry')
        entry.pack(fill='x')
        return entry

    def _show_login(self):
        card = self._card('Welcome back', 'Sign in to manage workloads, virtual machines, and scheduling results.')
        self.username = self._field(card, 'Username')
        self.password = self._field(card, 'Password', '*')
        self.message = ttk.Label(card, text='Demo account: admin / admin', style='AuthMuted.TLabel')
        self.message.pack(anchor='w', pady=(12, 14))
        ttk.Button(card, text='Sign In', style='AuthPrimary.TButton', command=self.login).pack(fill='x')
        links = tk.Frame(card, bg='#111c2e'); links.pack(fill='x', pady=(18, 0))
        ttk.Button(links, text='Create account', command=self._show_register).pack(side='left')
        ttk.Button(links, text='Forgot password?', command=self._show_forgot).pack(side='right')

    def _show_register(self):
        card = self._card('Create account', 'Set up a new scheduler account. New accounts start with the User role.')
        username = self._field(card, 'Username')
        email = self._field(card, 'Email')
        password = self._field(card, 'Password', '*')
        confirm = self._field(card, 'Confirm password', '*')
        message = ttk.Label(card, text='', style='AuthMuted.TLabel'); message.pack(anchor='w', pady=(12, 8))

        def register():
            values = [username.get().strip(), email.get().strip(), password.get(), confirm.get()]
            if not all(values) or password.get() != confirm.get():
                message.configure(text='Complete all fields and make sure passwords match.', foreground='#dc2626')
                return
            if len(password.get()) < 6 or '@' not in email.get():
                message.configure(text='Use a valid email and a password of at least 6 characters.', foreground='#dc2626')
                return
            try:
                with get_connection() as conn:
                    conn.execute('INSERT INTO users (username, email, role, status, password) VALUES (?, ?, ?, ?, ?)', (username.get().strip(), email.get().strip(), 'User', 'Active', password.get()))
                    conn.commit()
                self._show_login()
                self.message.configure(text='Account created. You can sign in now.', foreground='#15803d')
            except Exception as exc:
                message.configure(text='Username already exists or data is invalid.', foreground='#dc2626')

        ttk.Button(card, text='Create Account', style='AuthPrimary.TButton', command=register).pack(fill='x')
        ttk.Button(card, text='Back to sign in', command=self._show_login).pack(anchor='center', pady=(14, 0))

    def _show_forgot(self):
        card = self._card('Reset password', 'Enter the username and email linked to your account, then choose a new password.')
        username = self._field(card, 'Username')
        email = self._field(card, 'Email')
        password = self._field(card, 'New password', '*')
        confirm = self._field(card, 'Confirm new password', '*')
        message = ttk.Label(card, text='', style='AuthMuted.TLabel'); message.pack(anchor='w', pady=(12, 8))

        def reset():
            if not all((username.get().strip(), email.get().strip(), password.get(), confirm.get())) or password.get() != confirm.get():
                message.configure(text='Complete all fields and make sure passwords match.', foreground='#dc2626')
                return
            with get_connection() as conn:
                result = conn.execute('UPDATE users SET password = ? WHERE username = ? AND email = ?', (password.get(), username.get().strip(), email.get().strip()))
                conn.commit()
            if result.rowcount == 0:
                message.configure(text='No matching account was found.', foreground='#dc2626')
            else:
                self._show_login()
                self.message.configure(text='Password updated. Sign in with your new password.', foreground='#15803d')

        ttk.Button(card, text='Reset Password', style='AuthPrimary.TButton', command=reset).pack(fill='x')
        ttk.Button(card, text='Back to sign in', command=self._show_login).pack(anchor='center', pady=(14, 0))

    def login(self):
        username = self.username.get().strip()
        password = self.password.get().strip()
        if not username or not password:
            self.message.configure(text='Enter both username and password.', foreground='#dc2626')
            return
        with get_connection() as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? AND password = ? AND status = "Active"',
                (username, password)
            ).fetchone()
        if user is None:
            self.message.configure(text='Invalid credentials or inactive account.', foreground='#dc2626')
            return
        self.root.open_dashboard(dict(user))
