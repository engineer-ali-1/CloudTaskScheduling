import tkinter as tk
from tkinter import ttk

from .dashboard import Dashboard
from .login import LoginWindow


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Cloud Task Scheduling in Cloud Computing')
        self.geometry('1360x820')
        self.minsize(1080, 680)
        self.configure(bg='#0f172a')
        self.withdraw()

        self.login_window = LoginWindow(self)
        self.login_window.protocol('WM_DELETE_WINDOW', self.on_close)

    def on_close(self):
        self.destroy()

    def open_dashboard(self, user):
        self.login_window.destroy()
        self.deiconify()
        Dashboard(self, user)

    def show_login(self):
        for child in self.winfo_children():
            if child is not self.login_window:
                child.destroy()
        self.withdraw()
        self.login_window = LoginWindow(self)
        self.login_window.protocol('WM_DELETE_WINDOW', self.on_close)


if __name__ == '__main__':
    app = App()
    app.mainloop()
