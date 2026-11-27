"""Parsera: run with  python main.py"""
import tkinter as tk

from ui_common import C, UI, apply_theme, NavButton, FloatButton, pill
from splash import Splash
from tabs import Tab1, Tab2, Tab3, Tab4, Tab5, Tab6

NAMES = ['1   Grammar → Parse Tree', '2   Ambiguity Detect', '3   Make Unambiguous',
         '4   Parse Tree → AST', '5   Infix → Prefix/Postfix', '6   Operator Precedence']


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()                      # stay hidden while the welcome screen plays
        self.title('Parsera')
        # size the window to the screen so nothing (Exit button, player) falls under the taskbar
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(1260, sw - 60), min(830, sh - 140)
        self.geometry(f'{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2 - 30)}')
        self.minsize(900, 560)
        apply_theme(self)

        # ---- dark slate sidebar
        side = tk.Frame(self, bg=C['side'], width=280)
        side.pack(side='left', fill='y')
        side.pack_propagate(False)
        top = tk.Frame(side, bg=C['side'])
        top.pack(fill='x', padx=18, pady=(24, 22))
        logo = tk.Canvas(top, width=44, height=44, bg=C['side'], highlightthickness=0)
        logo.pack(side='left')
        pill(logo, 0, 0, 44, 44, C['ac'], C['teal'], r=13)
        logo.create_text(22, 22, text='λ', fill='#ffffff', font=(UI[0], 18, 'bold'))
        tk.Label(top, text='Parsera', bg=C['side'], fg='#ffffff', font=(UI[0], 16, 'bold')).pack(side='left', padx=12)

        # ---- footer card (like the user card in the dashboard)
        foot = tk.Frame(side, bg=C['side2'], padx=14, pady=14)
        foot.pack(side='bottom', fill='x', padx=14, pady=(18, 84))
        row = tk.Frame(foot, bg=C['side2'])
        row.pack(fill='x')
        av = tk.Canvas(row, width=40, height=40, bg=C['side2'], highlightthickness=0)
        av.create_oval(2, 2, 38, 38, fill=C['teal'], outline='')
        av.create_text(20, 20, text='P', fill='#ffffff', font=(UI[0], 13, 'bold'))
        av.pack(side='left')
        col = tk.Frame(row, bg=C['side2'])
        col.pack(side='left', padx=10)
        tk.Label(col, text='Parsera Studio', bg=C['side2'], fg='#ffffff', font=(UI[0], 10, 'bold'), anchor='w').pack(fill='x')
        tk.Label(col, text='Compiler construction', bg=C['side2'], fg='#aeb8cc', font=(UI[0], 9), anchor='w').pack(fill='x')

        # ---- content area
        body = tk.Frame(self, bg=C['bg'])
        body.pack(side='left', fill='both', expand=True, padx=22, pady=14)
        sh = {'tree': None, 'w': None}
        self.tabs = []
        for i, cls in enumerate((Tab1, Tab2, Tab3, Tab4, Tab5, Tab6)):
            t = cls(body, sh)
            sh[f't{i + 1}'] = t
            t.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.tabs.append(t)

        # ---- navigation
        self.btns = []
        for i, n in enumerate(NAMES):
            b = NavButton(side, n, lambda i=i: self.show(i))
            b.pack(fill='x', pady=2)
            self.btns.append(b)
        self.cur = 0
        self.bind_all('<MouseWheel>', self.wheel)
        self.bind_all('<Button-4>', self.wheel)
        self.bind_all('<Button-5>', self.wheel)
        self.show(0)
        # ---- floating exit button, hovering at the bottom of the sidebar
        FloatButton(side, 'Exit', self.destroy).place(relx=.5, rely=1.0, y=-8, anchor='s')
        self.update_idletasks()
        Splash(self, self.ready)

    def ready(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def show(self, i):
        self.cur = i
        self.tabs[i].tkraise()
        for j, b in enumerate(self.btns):
            b.set_active(i == j)
        self.tabs[i].on_show()

    def wheel(self, e):
        d = -3 if (getattr(e, 'num', 0) == 4 or getattr(e, 'delta', 0) > 0) else 3
        self.tabs[self.cur].cv.yview_scroll(d, 'units')


if __name__ == '__main__':
    App().mainloop()
