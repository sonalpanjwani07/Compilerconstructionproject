"""Welcome / loading screen of Parsera: a soft borderless window with a fading logo and a progress bar."""
import math
import time
import tkinter as tk

from ui_common import C, UI, mix, pill, rr

STEPS = [(0.00, 'Starting Parsera...'), (0.25, 'Loading the grammar engine...'),
         (0.50, 'Preparing parse trees...'), (0.75, 'Stacking the coins...'), (0.92, 'Almost ready...')]


class Splash(tk.Toplevel):
    W, H, TOTAL = 640, 390, 3.0

    def __init__(self, master, on_done):
        super().__init__(master)
        self.on_done, self.t0, self.dy = on_done, time.perf_counter(), 0.0
        self.overrideredirect(True)
        W, H = self.W, self.H
        x, y = (self.winfo_screenwidth() - W) // 2, (self.winfo_screenheight() - H) // 2 - 20
        self.geometry(f'{W}x{H}+{x}+{y}')
        self._alpha(0)
        try:
            self.attributes('-topmost', True)
        except tk.TclError:
            pass
        cv = self.cv = tk.Canvas(self, width=W, height=H, bg=C['side'], highlightthickness=0)
        cv.pack()
        for r in range(H):                                            # vertical gradient background
            cv.create_line(0, r, W, r, fill=mix('#0f1524', '#243252', r / H))
        for cx, cy, rad, col in ((W - 30, 20, 170, C['teal']), (30, H - 10, 150, C['ac'])):   # soft glow blobs
            for k in range(6, 0, -1):
                cv.create_oval(cx - rad * k / 6, cy - rad * k / 6, cx + rad * k / 6, cy + rad * k / 6,
                               fill=mix('#141b2b', col, .035 * (7 - k)), outline='')
        pill(cv, W / 2 - 44, 62, W / 2 + 44, 150, C['ac'], C['teal'], r=26, tag='logo')
        cv.create_text(W / 2, 106, text='\u03bb', fill='#ffffff', font=(UI[0], 42, 'bold'), tags='logo')
        cv.create_text(W / 2, 188, text='Welcome to', fill='#aeb8cc', font=(UI[0], 15))
        cv.create_text(W / 2, 232, text='Parsera', fill='#ffffff', font=(UI[0], 38, 'bold'))
        cv.create_text(W / 2, 278, text='See grammars, parse trees and stacks come alive', fill='#8f9bb5',
                       font=(UI[0], 11))
        self.bx1, self.bx2, self.by = W / 2 - 150, W / 2 + 150, 318
        cv.create_polygon(*rr(self.bx1, self.by, self.bx2, self.by + 10, 5), smooth=True, fill='#2a3550', outline='')
        self.msg = cv.create_text(W / 2, 354, text=STEPS[0][1], fill='#8f9bb5', font=(UI[0], 10))
        self._tick()

    def _alpha(self, a):
        try:
            self.attributes('-alpha', max(0.0, min(1.0, a)))
        except tk.TclError:
            pass

    def _tick(self):
        el = time.perf_counter() - self.t0
        k = max(0.0, min(1.0, (el - .25) / (self.TOTAL - .85)))
        e = k * k * (3 - 2 * k)                                           # smoothstep
        self._alpha(min(1.0, el / .35) if el < self.TOTAL - .35 else (self.TOTAL - el) / .35)
        self.cv.delete('bar')
        w = max(10, int((self.bx2 - self.bx1) * e))
        pill(self.cv, self.bx1, self.by, self.bx1 + w, self.by + 10, C['ac'], C['teal'], tag='bar')
        self.cv.itemconfigure(self.msg, text=[m for p, m in STEPS if k >= p][-1])
        d = math.sin(el * 3) * 4                                          # logo hovers gently
        self.cv.move('logo', 0, d - self.dy)
        self.dy = d
        if el >= self.TOTAL:
            self.destroy()
            self.on_done()
        else:
            self.after(30, self._tick)
