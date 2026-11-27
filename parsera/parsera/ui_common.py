"""Parsera theme: "Paper Clean" (dark slate sidebar, light paper page, white cards, blue to teal gradients)
and shared GUI helpers (animated tree, 3D coin stack, chips, player) in a single file."""
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

C = dict(bg='#f3f5f9', bg2='#f0f2f8', p='#ffffff', p2='#f5f7fb', tx='#232b3e', mu='#6f778c',
         ac='#2b7bdc', teal='#22b2a2', ok='#38a85c', er='#e0455f', ln='#e6e9f1', nd='#c3cad9',
         side='#141b2b', side2='#1f2a40')
UI = ('Segoe UI', 11)
MONO = ('Consolas', 12)


def apply_theme(root):
    root.configure(bg=C['bg'])
    s = ttk.Style(root)
    s.theme_use('clam')
    s.configure('.', background=C['p'], foreground=C['tx'], fieldbackground=C['p2'], bordercolor=C['ln'],
                lightcolor=C['p'], darkcolor=C['p'], troughcolor=C['p2'], font=UI)
    s.configure('TCombobox', fieldbackground=C['p2'], background=C['p2'], foreground=C['tx'], arrowcolor=C['ac'],
                bordercolor=C['ln'], padding=4)
    s.map('TCombobox', fieldbackground=[('readonly', C['p2'])], foreground=[('readonly', C['tx'])])
    s.configure('Horizontal.TScale', background=C['p'], troughcolor=C['ln'])
    for o in ('Vertical', 'Horizontal'):
        s.configure(f'{o}.TScrollbar', background='#cfd4de', troughcolor=C['bg'], arrowcolor=C['ac'], bordercolor=C['bg'])
    for k, v in (('Listbox.background', C['p']), ('Listbox.foreground', C['tx']),
                 ('Listbox.selectBackground', C['ac']), ('Listbox.selectForeground', '#ffffff')):
        root.option_add('*TCombobox*' + k, v)


# ---------------------------------------------------------------- colors and gradients
def mix(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def pill(cv, x1, y1, x2, y2, c1, c2, r=None, tag='g'):
    """Horizontal gradient inside a rounded rectangle, drawn column by column on a Canvas."""
    h, w = y2 - y1, int(x2 - x1)
    r = h / 2 if r is None else r
    for i in range(w):
        dx = min(i, w - 1 - i)
        inset = 0 if dx >= r else r - (r * r - (r - dx) ** 2) ** .5
        cv.create_line(x1 + i, y1 + inset, x1 + i, y2 - inset + 1, fill=mix(c1, c2, i / max(1, w - 1)), tags=tag)


def rr(x1, y1, x2, y2, r=10):
    return [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r, x2, y2 - r, x2, y2 - r,
            x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r,
            x1, y1 + r, x1, y1]


# ---------------------------------------------------------------- small widget helpers
class Rounded(tk.Frame):
    """Rounded panel with an optional soft shadow. It is built from ordinary packed widgets, so its size always
    follows its content: a background canvas is placed behind .inner, and .inner is packed with padding.
    face() returns .inner with pack / grid / place acting on the whole panel."""

    def __init__(self, m, fill=None, line='', pad=16, r=18, shadow=False):
        page = m.cget('bg')
        super().__init__(m, bg=page)
        self.page, self.fill, self.line, self.r, self.sh = page, fill or C['p'], line, r, 4 if shadow else 0
        self.bgc = tk.Canvas(self, bg=page, highlightthickness=0)
        self.bgc.place(x=0, y=0, relwidth=1, relheight=1)
        self.inner = tk.Frame(self, bg=self.fill)
        self.inner.pack(fill='both', expand=True, padx=pad, pady=(pad, pad + self.sh))
        self.bgc.bind('<Configure>', self._conf)

    def _conf(self, e):
        w, h = e.width, e.height
        c = self.bgc
        c.delete('all')
        r = max(4, min(self.r, (h - self.sh) / 2 - 1))
        if self.sh:
            c.create_polygon(*rr(2, 5, w - 2, h - 1, r), smooth=True, fill=mix(self.page, '#8a93ad', .12), outline='')
        c.create_polygon(*rr(1, 1, w - 1, h - 1 - self.sh, r), smooth=True, fill=self.fill, outline=self.line,
                         tags='body')

    def set_line(self, col):
        self.line = col
        self.bgc.itemconfigure('body', outline=col)

    def face(self, widget=None):
        w = widget or self.inner
        for n in ('pack', 'grid', 'place', 'pack_forget', 'grid_remove', 'grid_forget', 'place_forget'):
            setattr(w, n, getattr(self, n))
        return w


def card(m):
    """White rounded card with a soft shadow."""
    return Rounded(m, C['p'], '', pad=22, r=22, shadow=True).face()


def _field(m, make):
    """Input field inside a soft rounded box that turns blue while it has focus."""
    box = Rounded(m, C['p2'], C['ln'], pad=7, r=12)
    w = make(box.inner)
    w.pack(fill='both', expand=True, ipady=3, padx=4)
    box.face(w)
    w.bind('<FocusIn>', lambda e: box.set_line(C['ac']))
    w.bind('<FocusOut>', lambda e: box.set_line(C['ln']))
    return w


def lbl(m, text='', mu=False, bold=False, size=None, **kw):
    return tk.Label(m, text=text, bg=m['bg'], fg=C['mu'] if mu else C['tx'], anchor='w', justify='left',
                    font=(UI[0], size or 11, 'bold') if bold else (UI[0], size or 11), wraplength=860, **kw)


class StepBar(tk.Label):
    """One-line explanation of the current step: a soft blue strip (red for errors), invisible when empty."""

    def __init__(self, m):
        super().__init__(m, text='', bg=C['p'], fg=C['tx'], anchor='w', justify='left', wraplength=820,
                         font=(UI[0], 11, 'bold'), padx=14, pady=0)

    def config(self, **kw):
        super().config(**kw)
        on = bool(self['text'])
        super().config(bg=('#fdecef' if self['fg'] == C['er'] else '#eaf2fd') if on else C['p'], pady=9 if on else 0)

    configure = config


def txt(m, h=4):
    return _field(m, lambda p: tk.Text(p, height=h, bg=C['p2'], fg=C['tx'], insertbackground=C['tx'], font=MONO,
                                       relief='flat', bd=0, highlightthickness=0, wrap='word', padx=6, pady=4))


def entry(m, width=40, **kw):
    return _field(m, lambda p: tk.Entry(p, width=width, bg=C['p2'], fg=C['tx'], insertbackground=C['tx'],
                                        font=MONO, relief='flat', bd=0, highlightthickness=0, **kw))


def combo(m, values, width=30):
    return ttk.Combobox(m, values=values, state='readonly', width=width)


def set_text(w, s):
    w.configure(state='normal')
    w.delete('1.0', 'end')
    w.insert('1.0', s)


class GradButton(tk.Canvas):
    """Rounded button: blue to teal gradient (accent) or white with border. Supports .config(text=..., command=...)."""

    def __init__(self, m, text, command=None, accent=False):
        self.text, self.cmd, self.accent = text, command, accent
        self.font = tkfont.Font(font=(UI[0], 11, 'bold'))
        try:
            bg = m.cget('bg')
        except tk.TclError:
            bg = C['p']
        super().__init__(m, width=self._bw(), height=38, bg=bg, highlightthickness=0, cursor='hand2')
        self.bind('<Enter>', lambda e: self._draw(True))
        self.bind('<Leave>', lambda e: self._draw())
        self.bind('<ButtonRelease-1>', self._click)
        self._draw()

    def _bw(self):
        return max(46, self.font.measure(self.text) + 36)

    def _click(self, e):
        if self.cmd and 0 <= e.x <= int(self['width']) and 0 <= e.y <= int(self['height']):
            self.cmd()

    def _draw(self, hov=False):
        self.delete('all')
        w, h = int(self['width']), int(self['height'])
        if self.accent:
            pill(self, 0, 0, w, h, '#1b6fd0' if not hov else '#2a80e8', '#1fae9f' if not hov else '#2cc4b3')
        else:
            self.create_polygon(*rr(1, 1, w - 1, h - 1, h // 2), smooth=True, fill=C['p2'] if hov else C['p'],
                                outline=C['nd'] if hov else C['ln'])
        self.create_text(w / 2, h / 2, text=self.text, font=self.font, fill='#ffffff' if self.accent else C['tx'])

    def config(self, **kw):
        if 'text' in kw:
            self.text = kw.pop('text')
            super().config(width=self._bw())
            self._draw()
        if 'command' in kw:
            self.cmd = kw.pop('command')
        if kw:
            super().config(**kw)

    configure = config


def btn(m, text, cmd, accent=False):
    return GradButton(m, text, cmd, accent)


class NavButton(tk.Canvas):
    """Sidebar item: transparent on indigo, blue to teal gradient pill when active."""

    def __init__(self, m, text, cmd, h=44):
        super().__init__(m, height=h, bg=C['side'], highlightthickness=0, cursor='hand2')
        self.text, self.cmd, self.on, self.hov = text, cmd, False, False
        self.bind('<Configure>', lambda e: self.draw())
        self.bind('<Enter>', lambda e: self._h(True))
        self.bind('<Leave>', lambda e: self._h(False))
        self.bind('<ButtonRelease-1>', lambda e: self.cmd())

    def _h(self, v):
        self.hov = v
        self.draw()

    def set_active(self, v):
        self.on = v
        self.draw()

    def draw(self):
        self.delete('all')
        w, h = self.winfo_width(), int(self['height'])
        if w < 20:
            return
        if self.on:
            pill(self, 8, 4, w - 8, h - 4, C['ac'], C['teal'])
        elif self.hov:
            pill(self, 8, 4, w - 8, h - 4, C['side2'], C['side2'])
        self.create_text(26, h / 2, text=self.text, anchor='w', fill='#ffffff' if self.on else '#aeb8cc',
                         font=(UI[0], 12, 'bold' if self.on else 'normal'))


class FloatButton(tk.Canvas):
    """Soft coral pill that hovers with a gentle bob and a shadow; lifts and brightens on hover."""

    def __init__(self, m, text, command, w=176, h=46):
        self.text, self.cmd, self.bw, self.bh, self.hov, self.cur, self.t = text, command, w, h, False, 0.0, 0.0
        super().__init__(m, width=w, height=h + 22, bg=m['bg'], highlightthickness=0, cursor='hand2')
        self.font = tkfont.Font(font=(UI[0], 12, 'bold'))
        self.bind('<Enter>', lambda e: self._h(True))
        self.bind('<Leave>', lambda e: self._h(False))
        self.bind('<ButtonRelease-1>', lambda e: self.cmd())
        self._draw()
        self._bob()

    def _h(self, v):
        self.hov = v
        self._draw()

    def _draw(self):
        self.delete('all')
        w, h = self.bw, self.bh
        base = self['bg']
        for k, t in ((1.0, .35), (.84, .6), (.68, .85)):          # soft floor shadow
            self.create_oval(w / 2 - (w / 2 - 14) * k, h + 8 - 5 * k, w / 2 + (w / 2 - 14) * k, h + 8 + 5 * k,
                             fill=mix(base, '#05080f', t), outline='', tags='sh')
        c1, c2 = ('#ff8f86', '#ef5a73') if self.hov else ('#f77f7f', '#e0455f')
        pill(self, 8, 4, w - 8, 4 + h, c1, c2, tag='btn')
        self.create_text(w / 2, 4 + h / 2, text='\u2715   ' + self.text, font=self.font, fill='#ffffff', tags='btn')
        self.move('btn', 0, self.cur - (3 if self.hov else 0))

    def _bob(self):
        import math
        self.t += .06
        d = math.sin(self.t) * 3
        self.move('btn', 0, d - self.cur)
        self.cur = d
        self.after(40, self._bob)


def drop(cv, tag, dy=-44, steps=10):
    """Slide-in animation for newly pushed stack/output items."""
    cv.move(tag, 0, dy)
    d, n = -dy / steps, [0]

    def f():
        n[0] += 1
        cv.move(tag, 0, d)
        if n[0] < steps:
            cv._dj = cv.after(24, f)
    cv._dj = cv.after(24, f)


def _cancel(cv):
    j = getattr(cv, '_dj', None)
    if j:
        cv.after_cancel(j)
        cv._dj = None


# ---------------------------------------------------------------- animated tree
def layout(roots):
    pos, order, X, mx = {}, [], [0], [0]

    def go(n, d, par):
        mx[0] = max(mx[0], d)
        order.append(n.id)
        if not n.k:
            w = max(56, len(n.l) * 9 + 24)
            pos[n.id] = (X[0] + w / 2, d * 64 + 30, n, par)
            X[0] += w
        else:
            for c in n.k:
                go(c, d + 1, n.id)
            pos[n.id] = ((pos[n.k[0].id][0] + pos[n.k[-1].id][0]) / 2, d * 64 + 30, n, par)
    for r in roots:
        go(r, 0, None)
        X[0] += 30
    return pos, order, X[0], (mx[0] + 1) * 64 + 20


class TreeCanvas(tk.Frame):
    """Soft parse-tree drawing inside one rounded panel: non-terminals are blue bubbles, terminals teal pills,
    the node being expanded glows green. Nodes glide to their new positions and new nodes grow out of their
    parent. Scrollbars only appear when the tree is bigger than the panel."""

    def __init__(self, m, height=250, legend=False):
        super().__init__(m, bg=C['p'])
        panel = Rounded(self, C['bg2'], '', pad=10, r=18)
        panel.grid(row=0, column=0, sticky='nsew')
        box = panel.inner
        self.c = tk.Canvas(box, bg=C['bg2'], width=300, height=height, highlightthickness=0)
        self.hs = ttk.Scrollbar(box, orient='horizontal', command=self.c.xview)
        self.vs = ttk.Scrollbar(box, command=self.c.yview)
        self.c.configure(xscrollcommand=self.hs.set, yscrollcommand=self.vs.set)
        self.c.grid(row=0, column=0, sticky='nsew')
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)
        self.region, self.vshow, self.hshow = None, False, False
        self.c.bind('<Configure>', lambda e: self._bars())
        if legend:
            self.key().grid(row=1, column=0, sticky='w', pady=(8, 0))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.items, self.cur, self.job = {}, {}, None

    def _bars(self):
        """Show a scrollbar only when the tree does not fit (sizes are judged as if no bar were shown)."""
        if not self.region:
            return
        x2, y2 = self.region
        w = self.c.winfo_width() + (15 if self.vshow else 0)
        h = self.c.winfo_height() + (15 if self.hshow else 0)
        nv, nh = y2 > h, x2 > w
        if nh and not nv:
            nv = y2 > h - 15
        if nv and not nh:
            nh = x2 > w - 15
        if nv != self.vshow:
            self.vshow = nv
            self.vs.grid(row=0, column=1, sticky='ns') if nv else self.vs.grid_remove()
        if nh != self.hshow:
            self.hshow = nh
            self.hs.grid(row=1, column=0, sticky='ew') if nh else self.hs.grid_remove()

    def key(self):
        """How to read the tree: one coloured dot per node type."""
        f = tk.Frame(self, bg=C['p'])
        for col, text in ((C['ac'], 'Blue bubble = non-terminal (can still expand)'),
                          (C['teal'], 'Teal pill = terminal (final symbol)'),
                          (C['ok'], 'Green glow = expanding now')):
            tk.Label(f, text='\u25cf', bg=C['p'], fg=col, font=(UI[0], 13)).pack(side='left')
            tk.Label(f, text=text, bg=C['p'], fg=C['mu'], font=(UI[0], 10)).pack(side='left', padx=(2, 16))
        return f

    def draw(self, roots, hl=None):
        c = self.c
        pos, order, W, Hh = layout(roots)
        cw = c.winfo_width()
        off = max(0, (cw - W) / 2) if cw > 60 else 0                    # centre small trees
        pos = {i: (x + off, y, n, par) for i, (x, y, n, par) in pos.items()}
        self.region = (W + 20, Hh)
        c.configure(scrollregion=(0, 0, W + 20, Hh))
        self._bars()
        for i in [i for i in self.items if i not in pos]:
            for it in self.items.pop(i)['ids']:
                c.delete(it)
            self.cur.pop(i, None)
        start = {}
        for i in order:
            x, y, n, par = pos[i]
            if i not in self.items:
                ids = [c.create_polygon(0, 0, 0, 0, smooth=True, fill='#dfe3ee', outline=''),       # 0 soft shadow
                       c.create_polygon(0, 0, 0, 0, smooth=True, fill='#cdeed9', outline=''),       # 1 green glow
                       c.create_polygon(0, 0, 0, 0, smooth=True, width=2),                          # 2 body
                       c.create_text(0, 0, font=(MONO[0], MONO[1], 'bold'), text=n.l),             # 3 label
                       c.create_line(0, 0, 0, 0, 0, 0, 0, 0, smooth=True, fill='#bcc6da', width=2)]  # 4 edge
                c.tag_lower(ids[4])
                self.items[i] = dict(ids=ids, w=max(34, len(n.l) * 9 + 16))
                self.cur[i] = dict(self.cur.get(par, {'x': x, 'y': y}))
            start[i] = dict(self.cur[i])
            hot = bool(hl and i in hl)
            ids = self.items[i]['ids']
            if hot:
                fill, line, fg = '#e3f6e9', C['ok'], '#1f7a3a'
            elif n.t:
                fill, line, fg = '#d9f4ef', '#7fd3c7', '#0f7f73'
            else:
                fill, line, fg = '#eaf2fd', '#8db8ef', C['ac']
            c.itemconfigure(ids[1], state='normal' if hot else 'hidden')
            c.itemconfigure(ids[2], fill=fill, outline=line)
            c.itemconfigure(ids[3], fill=fg)
        if self.job:
            self.after_cancel(self.job)
        t0 = time.perf_counter()

        def step():
            k = min(1.0, (time.perf_counter() - t0) / 0.55)
            e = 2 * k * k if k < .5 else 1 - (-2 * k + 2) ** 2 / 2
            for i in order:
                x, y, _, par = pos[i]
                a, cu = start[i], self.cur[i]
                cu['x'], cu['y'] = a['x'] + (x - a['x']) * e, a['y'] + (y - a['y']) * e
                sh, gl, body, tx, ln = self.items[i]['ids']
                w = self.items[i]['w'] / 2
                c.coords(sh, *rr(cu['x'] - w + 1, cu['y'] - 14, cu['x'] + w + 1, cu['y'] + 20, 17))
                c.coords(gl, *rr(cu['x'] - w - 6, cu['y'] - 22, cu['x'] + w + 6, cu['y'] + 22, 22))
                c.coords(body, *rr(cu['x'] - w, cu['y'] - 17, cu['x'] + w, cu['y'] + 17, 17))
                c.coords(tx, cu['x'], cu['y'])
                if par is not None and par in self.cur:
                    p = self.cur[par]
                    my = (p['y'] + cu['y']) / 2
                    c.coords(ln, p['x'], p['y'] + 12, p['x'], my, cu['x'], my, cu['x'], cu['y'] - 12)
                    c.itemconfigure(ln, state='normal')
                else:
                    c.itemconfigure(ln, state='hidden')
            self.job = self.after(16, step) if k < 1 else None
        step()


# ---------------------------------------------------------------- coin stack and chips
PRIO = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2, '^': 3, '**': 3}
# (top face, side) colours of every coin / chip kind
COIN = {1: ('#3b8ae6', '#1459ad'), 2: ('#2cc0ae', '#16897d'), 3: ('#8a6be0', '#5238a8'),
        'br': ('#43b866', '#27803f'), 'bot': ('#98a1b3', '#6b7487'),
        'nt': ('#eef1f7', '#b3bbcc'), 'op': ('#f0c05a', '#b98419')}


def coin_kind(sym, nt=False):
    """Colour key and caption of one stack symbol."""
    if nt:
        return 'nt', 'non-terminal'
    if sym == '$':
        return 'bot', 'bottom marker'
    if sym in ('(', ')'):
        return 'br', 'bracket'
    if sym in PRIO:
        return PRIO[sym], f'priority {PRIO[sym]}'
    return 'op', 'operand'


class StackView(tk.Canvas):
    """3D coin stack: every symbol is a coin with its priority beside it, a soft shadow on the floor,
    and the newest coin drops in from above."""

    def __init__(self, m, w=250, h=300):
        super().__init__(m, width=w, height=h, bg=C['p'], highlightthickness=0)

    def _shadow(self, cx, cy, rx, ry):
        for k, t in ((1.0, .30), (.82, .55), (.64, .80)):
            self.create_oval(cx - rx * k, cy - ry * k, cx + rx * k, cy + ry * k, fill=mix(C['bg2'], '#aab1c2', t),
                             outline='')

    def show(self, items, new=False, nts=(), top=None):
        _cancel(self)
        self.delete('all')
        W, Hh, n = int(self['width']), int(self['height']), len(items)
        self.create_polygon(*rr(1, 1, W - 1, Hh - 1, 22), smooth=True, fill=C['bg2'], outline='')
        cx, rx, ry, th = 92, 56, 15, 13
        y0 = Hh - 46
        self._shadow(cx, Hh - 31, rx + 14, ry + 3)
        if not n:
            self.create_text(cx, Hh - 74, text='Stack is empty', fill=C['mu'], font=(UI[0], 9))
            return
        step = min(17, (y0 - ry - 12) / max(n - 1, 1))
        for i, t in enumerate(items):
            yc = y0 - i * step
            key, cap = coin_kind(t, i in nts)
            light, dark = COIN[key]
            tag = f'i{i}'
            self.create_oval(cx - rx, yc + th - ry, cx + rx, yc + th + ry, fill=dark, outline=dark, tags=tag)
            self.create_rectangle(cx - rx, yc, cx + rx, yc + th, fill=dark, outline=dark, tags=tag)
            self.create_oval(cx - rx, yc - ry, cx + rx, yc + ry, fill=light, outline=dark,
                             width=3 if i == top else 1, tags=tag)
            if i == top:
                self.create_oval(cx - rx, yc - ry, cx + rx, yc + ry, outline=C['ok'], width=3, tags=tag)
            self.create_oval(cx - rx + 8, yc - ry + 4, cx + rx - 8, yc + ry - 4, outline=mix(light, '#ffffff', .45),
                             tags=tag)
            self.create_text(cx, yc, text=t, font=(MONO[0], 12, 'bold'), tags=tag,
                             fill=C['tx'] if key in ('nt', 'op') else '#ffffff')
            self.create_text(cx + rx + 12, yc, text=cap, anchor='w', fill=C['mu'], font=(UI[0], 9), tags=tag)
        if new:
            drop(self, f'i{n - 1}')


class ChipRow(tk.Canvas):
    """Wrapping row of chips (input tape, derivation ribbon or output tray).
    tray=True draws a dashed tray; colored=True colours operators like their coins;
    cap = small caption on top; kinds = per-chip 'new' / 'nt' / 't' for the derivation ribbon."""

    def __init__(self, m, w=560, tray=False, colored=False, cap=''):
        super().__init__(m, width=w, height=44, bg=C['p'], highlightthickness=0)
        self.f, self.W, self.tray, self.colored, self.cap = tkfont.Font(font=MONO), w, tray, colored, cap

    def show(self, items, on=None, dn=0, new=False, kinds=None):
        _cancel(self)
        self.delete('all')
        y0 = 24 if self.cap else 8
        x, y, W = 8, y0, max(self.winfo_width(), self.W)
        if self.cap:
            self.create_text(10, 4, text=self.cap, anchor='nw', fill=C['mu'], font=(UI[0], 9))
        for i, t in enumerate(items):
            w = self.f.measure(t) + 24
            if x + w > W - 8 and x > 8:
                x, y = 8, y + 36
            kind = kinds[i] if kinds else None
            fill, line, fg = C['p'], C['nd'], (C['mu'] if i < dn else C['tx'])
            if i == on or kind == 'new':
                fill, line, fg = C['ac'], C['ac'], '#ffffff'
            elif kind == 'nt':
                fill, line, fg = '#e8f1fc', C['ac'], C['ac']
            elif self.colored and t in PRIO:
                fill, line, fg = COIN[PRIO[t]][0], COIN[PRIO[t]][1], '#ffffff'
            self.create_polygon(*rr(x, y, x + w, y + 28, 8), smooth=True, fill=fill, outline=line, tags=f'c{i}')
            self.create_text(x + w / 2, y + 14, text=t, font=(MONO[0], MONO[1], 'bold'), tags=f'c{i}', fill=fg)
            x += w + 6
        h = y + 44
        self.configure(height=h)
        if self.tray:
            self.create_polygon(*rr(3, 3, W - 3, h - 3, 16), smooth=True, fill='', outline=C['ac'], width=2,
                                dash=(5, 3))
        if new and items:
            drop(self, f'c{len(items) - 1}')


# ---------------------------------------------------------------- player
class Player(tk.Frame):
    """Restart / Back / Start-Pause / Next controls, a progress bar, step counter and a speed box.
    Frames are given with load(F, auto=True); auto=True starts playing at once."""
    SPEEDS = {'Slow': 1600, 'Normal': 1000, 'Fast': 450}

    def __init__(self, m, render):
        super().__init__(m, bg=C['p'])
        self.render, self.F, self.i, self.job, self.lock = render, [], 0, None, False

        def B(t, cmd, accent=False):
            b = btn(self, t, cmd, accent)
            b.pack(side='left', padx=3)
            return b
        B('↺ Restart', self.restart)
        B('◀ Back', lambda: self.jump(self.i - 1))
        self.pb = B('▶ Start', self.toggle, True)
        B('Next ▶', lambda: self.jump(self.i + 1))
        self.seek = ttk.Scale(self, from_=0, to=1, length=220, command=self._seek)
        self.seek.pack(side='left', padx=10)
        self.cnt = tk.Label(self, bg=C['p'], fg=C['mu'], font=UI, width=12)
        self.cnt.pack(side='left')
        tk.Label(self, text='Speed', bg=C['p'], fg=C['mu'], font=UI).pack(side='left', padx=(6, 4))
        self.spd = ttk.Combobox(self, values=list(self.SPEEDS), state='readonly', width=8)
        self.spd.set('Normal')
        self.spd.pack(side='left')

    def delay(self):
        return self.SPEEDS.get(self.spd.get(), 1000)

    def _label(self):
        last = len(self.F) > 1 and self.i >= len(self.F) - 1
        self.pb.config(text='❚❚ Pause' if self.job else '↺ Replay' if last else '▶ Start' if self.i == 0 else '▶ Resume')

    def go(self, n):
        if not self.F:
            self.cnt.config(text='Step 0 / 0')
            self._label()
            return
        self.i = max(0, min(len(self.F) - 1, n))
        self.lock = True
        self.seek.configure(to=max(1, len(self.F) - 1))
        self.seek.set(self.i)
        self.lock = False
        self.cnt.config(text=f'Step {self.i + 1} / {len(self.F)}')
        self._label()
        self.render(self.F[self.i])

    def _seek(self, v):
        if not self.lock:
            self.stop()
            self.go(round(float(v)))

    def jump(self, n):
        self.stop()
        self.go(n)

    def restart(self):
        self.stop()
        self.go(0)
        if len(self.F) > 1:
            self.toggle()

    def stop(self):
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        self._label()

    def toggle(self):
        if self.job:
            return self.stop()
        if self.i >= len(self.F) - 1:
            self.go(0)
        self.job = self.after(self.delay(), self._tick)
        self._label()

    def _tick(self):
        if self.i >= len(self.F) - 1:
            self.job = None
            self.stop()
            return
        self.job = None
        self.go(self.i + 1)
        if self.i >= len(self.F) - 1:
            return self.stop()
        self.job = self.after(self.delay(), self._tick)
        self._label()

    def load(self, F, auto=False):
        self.stop()
        self.F = F
        self.go(0)
        if auto and len(F) > 1:
            self.toggle()


# ---------------------------------------------------------------- scrollable page
class Page(tk.Frame):
    """Vertically scrollable page; put content in self.body."""

    def __init__(self, m):
        super().__init__(m, bg=C['bg'])
        self.dock = tk.Frame(self, bg=C['bg'])          # fixed bar at the bottom, never scrolls away
        self.dock.pack(side='bottom', fill='x')
        self.cv = tk.Canvas(self, bg=C['bg'], highlightthickness=0)
        sb = ttk.Scrollbar(self, command=self.cv.yview)
        self.cv.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        self.cv.pack(side='left', fill='both', expand=True)
        self.body = tk.Frame(self.cv, bg=C['bg'])
        w = self.cv.create_window(0, 0, window=self.body, anchor='nw')
        self.cv.bind('<Configure>', lambda e: self.cv.itemconfigure(w, width=e.width))
        self.body.bind('<Configure>', lambda e: self.cv.configure(scrollregion=self.cv.bbox('all')))
