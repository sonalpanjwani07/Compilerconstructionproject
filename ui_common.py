"""Parsera theme: "Paper Clean" (dark slate sidebar, light paper page, white cards, blue to teal gradients)
and shared GUI helpers (animated tree, 3D coin stack, chips, player) in a single file."""
import math
import random
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


# ---------------------------------------------------------------- animated teacher + coin stack
def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _lerp(a, b, t):
    return a + (b - a) * t


def _seg(p, a, b):
    return max(0.0, min(1.0, (p - a) / (b - a)))


def _path(p, keys):
    """Eased piece-wise path through [(time, (x, y)), ...] keyframes."""
    if p <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if p <= t1:
            e = _ease((p - t0) / (t1 - t0))
            return _lerp(a[0], b[0], e), _lerp(a[1], b[1], e)
    return keys[-1][1]


SKIN, HAIR, INK, GOLD = '#f3c9a5', '#3a2f4f', '#232b3e', '#f0c05a'
CHEER = {'push': ['Nice!', 'Perfect!', 'Yes!', 'Great!'], 'pop': ['Got it!', 'Popped!', 'Ta-da!', 'Easy!']}


class StackView(tk.Canvas):
    """3D coin stack with an animated teacher (Prof. Lambda).
    Every time show() receives a stack that differs from the previous one, the teacher PUSHES (tosses a coin on
    top, then cheers) or POPS (flicks the top coin off, catches it with a surprised face, then smiles).
    A deeper change (e.g. a reduction that pops 3 coins and pushes 1) is played as a quick chain of operations.
    show(items, new, nts, top, mood=None, say=None): mood='oops' makes the teacher react to an error.
    .budget = seconds the animation may take (set it from the player speed)."""

    def __init__(self, m, w=390, h=300):
        super().__init__(m, width=w, height=h, bg=C['p'], highlightthickness=0)
        self.W, self.H, self.budget = w, h, .85
        self.cx, self.rx, self.ry, self.th = w - 168, 56, 15, 13          # coin geometry
        self.y0, self.tx, self.fy = h - 46, 64, h - 36                    # floor of coins, teacher x, teacher feet
        self.sy = self.fy - 92                                            # shoulder line of the teacher
        self.bf = tkfont.Font(font=(UI[0], 10, 'bold'))
        self.state, self.top, self.ops, self.cur, self.lg, self.pend, self.sparks = None, None, [], None, None, None, []
        self._static([])
        self._frame()

    # ------------------------------------------------------------ static part: floor, shadow, coins
    def _step(self, n):
        return min(17, (self.y0 - self.ry - 12) / max(n - 1, 1))

    def _coin(self, cx, yc, sym, nt, tag, s=1.0, fl=1.0, cap=False, top=False):
        key, caption = coin_kind(sym, nt)
        light, dark = COIN[key]
        rx, ry, th = self.rx * s, self.ry * s * fl, self.th * s * fl
        self.create_oval(cx - rx, yc + th - ry, cx + rx, yc + th + ry, fill=dark, outline=dark, tags=tag)
        self.create_rectangle(cx - rx, yc, cx + rx, yc + th, fill=dark, outline=dark, tags=tag)
        self.create_oval(cx - rx, yc - ry, cx + rx, yc + ry, fill=light, outline=dark, width=3 if top else 1, tags=tag)
        if top:
            self.create_oval(cx - rx, yc - ry, cx + rx, yc + ry, outline=C['ok'], width=3, tags=tag)
        self.create_oval(cx - rx + 8 * s, yc - ry + 4 * s * fl, cx + rx - 8 * s, yc + ry - 4 * s * fl,
                         outline=mix(light, '#ffffff', .45), tags=tag)
        if s * fl > .45:
            self.create_text(cx, yc, text=sym, font=(MONO[0], max(7, int(12 * s)), 'bold'), tags=tag,
                             fill=C['tx'] if key in ('nt', 'op') else '#ffffff')
        if cap:
            self.create_text(cx + rx + 12, yc, text=caption, anchor='w', fill=C['mu'], font=(UI[0], 9), tags=tag)

    def _static(self, state, top=None, step=None):
        self.delete('stk')
        W, Hh, n, cx = self.W, self.H, len(state), self.cx
        self.create_polygon(*rr(1, 1, W - 1, Hh - 1, 22), smooth=True, fill=C['bg2'], outline='', tags='stk')
        for k, t in ((1.0, .30), (.82, .55), (.64, .80)):
            self.create_oval(cx - (self.rx + 14) * k, Hh - 31 - (self.ry + 3) * k, cx + (self.rx + 14) * k,
                             Hh - 31 + (self.ry + 3) * k, fill=mix(C['bg2'], '#aab1c2', t), outline='', tags='stk')
        if not n:
            self.create_text(cx, Hh - 74, text='Stack is empty', fill=C['mu'], font=(UI[0], 9), tags='stk')
        step = step or self._step(n)
        for i, (t, nt) in enumerate(state):
            self._coin(cx, self.y0 - i * step, t, nt, 'stk', cap=True, top=(i == top))
        self.tag_lower('stk')

    # ------------------------------------------------------------ public API
    def show(self, items, new=False, nts=(), top=None, mood=None, say=None):
        nxt = [(t, i in nts) for i, t in enumerate(items)]
        old, self.state, self.top = self.state, nxt, top
        self.cur, self.ops, self.pend = None, [], ((mood, say) if mood else None)
        now = time.perf_counter()
        ops = self._plan(old or [], nxt) if old is not None else []
        if not ops or len(ops) > 5:                                    # nothing to act out (or a big jump): snap
            self._static(nxt, top)
            if self.pend:
                self._settle(now, None)
            return
        dur = max(.24, min(.7, self.budget / len(ops)))
        for o in ops:
            o['dur'] = dur
        self.ops = ops
        self._start(self.ops.pop(0), now)

    def _plan(self, old, new):
        k = 0
        while k < min(len(old), len(new)) and old[k] == new[k]:
            k += 1
        ops, cur = [], list(old)
        while len(cur) > k:
            ops.append(dict(kind='pop', coin=cur[-1], before=list(cur), after=cur[:-1], idx=len(cur) - 1))
            cur = cur[:-1]
        for j in range(k, len(new)):
            ops.append(dict(kind='push', coin=new[j], before=list(cur), after=cur + [new[j]], idx=len(cur)))
            cur = cur + [new[j]]
        for o in ops:
            o['step'] = self._step(max(len(o['before']), len(o['after'])))
            o['cheer'] = random.choice(CHEER[o['kind']])
            o['base'] = o['after'] if o['kind'] == 'pop' else o['before']
        return ops

    def _start(self, op, now):
        op['t0'], op['spk'] = now, False
        self.cur = op
        self._static(op['base'], None, op['step'])

    def _end_op(self, now):
        last = self.cur
        if self.ops:
            self._start(self.ops.pop(0), now)
            return
        self.cur = None
        self._static(self.state, self.top)
        self._settle(now, last)

    def _settle(self, now, last):
        """After the last operation: keep the reaction face and speech bubble for a moment."""
        if last:
            text = 'Empty!' if (last['kind'] == 'pop' and not self.state) else last['cheer']
            self.lg = dict(face='happy', t0=now, until=now + 1.4, bub=text)
        if self.pend:
            mood, say = self.pend
            self.lg = dict(face=mood, t0=now, until=now + 2.4, bub=say or 'Oops!')
            self.pend = None

    # ------------------------------------------------------------ frame loop
    def _frame(self):
        try:
            self.after(33, self._frame)
        except tk.TclError:
            return
        if not self.winfo_viewable():
            return
        now = time.perf_counter()
        op = self.cur
        p = 0.0
        if op:
            p = (now - op['t0']) / op['dur']
            if p >= 1:
                self._end_op(now)
                op, p = self.cur, 0.0
        self.delete('dyn')
        P = self._pose(op, p, now) if op else self._idle(now)
        self._draw(P, now)

    # ------------------------------------------------------------ poses
    def _top_xy(self):
        n = len(self.state or [])
        return self.cx, self.y0 - max(n - 1, 0) * self._step(n) - 20

    def _idle(self, now):
        tx, sy = self.tx, self.sy
        P = dict(by=0.0, R=(tx + 30, sy + 50), L=(tx - 30, sy + 46), face='smile', coin=None, bub=None,
                 look=self._top_xy(), shake=0.0, blink=(now * 1000) % 3800 < 130, ring=None)
        lg = self.lg
        if lg and now < lg['until']:
            q = now - lg['t0']
            P['face'], P['blink'] = lg['face'], False
            if q < 1.4:
                P['bub'] = lg['bub']
            if lg['face'] == 'happy' and q < .9:
                P['by'] = -abs(math.sin(q * 9)) * 6 * (1 - q / .9)
                P['L'] = (tx - 38, sy - 26 + math.sin(q * 14) * 5)
            if lg['face'] == 'oops' and q < 1.6:
                P['shake'] = math.sin(q * 34) * 2
        return P

    def _pose(self, op, p, now):
        tx, sy, cx = self.tx, self.sy, self.cx
        rest, lrest = (tx + 30, sy + 50), (tx - 30, sy + 46)
        ty = self.y0 - op['idx'] * op['step']
        sym, nt = op['coin']
        P = dict(by=0.0, L=lrest, face='focus', coin=None, bub=None, shake=0.0, blink=False, ring=None)
        if op['kind'] == 'push':
            R = _path(p, [(0, rest), (.2, (tx + 6, sy + 58)), (.45, (tx + 62, sy - 34)), (.75, (tx + 70, sy - 40)),
                          (1, rest)])
            P['bub'] = f"Push '{sym}'" if p < .75 else op['cheer']
            if p < .45:
                s = .85 * _ease(_seg(p, .03, .18))
                P['coin'] = (R[0], R[1] - 12, sym, nt, s, 1.0, False)
                P['look'] = (tx + 40, sy - 40)
            elif p < .75:
                u = (p - .45) / .30
                sx, sy_ = tx + 62, sy - 46
                x, y = _lerp(sx, cx, u), _lerp(sy_, ty, u) - 4 * 46 * u * (1 - u)
                P['coin'] = (x, y, sym, nt, _lerp(.85, 1, u), max(.25, abs(math.cos(u * math.pi * 2))), False)
                P['look'] = (x, y)
            else:
                u = _seg(p, .75, 1)
                fl = 1 - .22 * math.sin(math.pi * min(1, u * 2.5)) if u < .4 else 1
                P['coin'] = (cx, ty, sym, nt, 1.0, fl, False)
                P['face'] = 'happy'
                P['by'] = -abs(math.sin(u * math.pi * 2)) * 7
                P['L'] = (tx - 38, sy - 26 + math.sin(u * 20) * 5)
                P['look'] = (cx, ty)
                if u < .6:
                    P['ring'] = (cx, ty, u / .6)
                if not op['spk']:
                    op['spk'] = True
                    self._burst(cx, ty - 6, now)
        else:
            R = _path(p, [(0, rest), (.2, (tx + 64, sy - 30)), (.55, (tx + 66, sy - 32)), (.8, (tx + 44, sy - 58)),
                          (1, rest)])
            P['bub'] = f"Pop '{sym}'" if p < .55 else op['cheer']
            if p < .2:
                P['coin'] = (cx, ty - 3 * math.sin(p / .2 * math.pi), sym, nt, 1.0, 1.0, True)
                P['look'] = (cx, ty)
            elif p < .55:
                u = _ease((p - .2) / .35)
                ex, ey = R[0] + 6, R[1] - 14
                x, y = _lerp(cx, ex, u), _lerp(ty, ey, u) - 4 * 40 * u * (1 - u)
                P['coin'] = (x, y, sym, nt, _lerp(1, .85, u), max(.25, abs(math.cos(u * math.pi * 2))), False)
                P['look'] = (x, y)
            else:
                v = _seg(p, .8, 1)
                s = .85 * (1 - _ease(v))
                P['coin'] = (R[0] + 6, R[1] - 14, sym, nt, s, 1.0, False)
                P['look'] = (R[0], R[1])
                P['face'] = 'wow' if p < .72 else 'happy'
                P['L'] = (tx - 38, sy - 26 + math.sin((p - .55) * 40) * 5)
                P['by'] = -abs(math.sin((p - .55) / .45 * math.pi * 2)) * 5
                if p >= .8 and not op['spk']:
                    op['spk'] = True
                    self._burst(R[0] + 6, R[1] - 14, now)
        P['R'] = R
        return P

    def _burst(self, x, y, now):
        for k in range(6):
            a = k / 6 * math.tau + random.random() * .5
            self.sparks.append(dict(x=x, y=y, vx=math.cos(a) * 34, vy=math.sin(a) * 30 - 12, t0=now))

    # ------------------------------------------------------------ drawing the teacher
    def _arm(self, sx, sy, hx, hy, tag='dyn'):
        L = 34
        dx, dy = hx - sx, hy - sy
        d0 = math.hypot(dx, dy) or 1
        d = min(d0, 2 * L - .5)
        ux, uy = dx / d0, dy / d0
        hx, hy = sx + ux * d, sy + uy * d
        h = math.sqrt(max(L * L - (d / 2) ** 2, 0))
        mx, my = sx + ux * d / 2, sy + uy * d / 2
        a, b = (mx - uy * h, my + ux * h), (mx + uy * h, my - ux * h)
        ex, ey = a if a[1] > b[1] else b
        self.create_line(sx, sy, ex, ey, hx, hy, width=11, fill=C['ac'], capstyle='round', joinstyle='round', tags=tag)
        return hx, hy

    def _star(self, x, y, r, col):
        k = r * .32
        self.create_polygon(x, y - r, x + k, y - k, x + r, y, x + k, y + k, x, y + r, x - k, y + k, x - r, y,
                            x - k, y - k, fill=col, outline='', tags='dyn')

    def _draw(self, P, now):
        c, tx, fy = self.create_oval, self.tx, self.fy
        by = P['by'] + math.sin(now * 2.2) * 1.0
        sy = self.sy + by
        hx, hy = tx + P['shake'], sy - 30
        # ---- floor shadow
        for k, t in ((1.0, .30), (.8, .55), (.6, .80)):
            c(tx - 36 * k, fy + 5 - 6 * k, tx + 36 * k, fy + 5 + 6 * k, fill=mix(C['bg2'], '#aab1c2', t), outline='',
              tags='dyn')
        # ---- legs and shoes
        for dx in (-11, 11):
            self.create_rectangle(tx + dx - 6, fy - 44, tx + dx + 6, fy - 6, fill='#2a3350', outline='', tags='dyn')
            c(tx + dx - 11, fy - 11, tx + dx + 9, fy, fill='#141b2b', outline='', tags='dyn')
        # ---- left arm (behind), holding a little book
        lx, ly = self._arm(tx - 24, sy + 4, *P['L'])
        self.create_rectangle(lx - 9, ly - 9, lx + 9, ly + 11, fill=C['teal'], outline='#16897d', width=2, tags='dyn')
        self.create_line(lx - 4, ly - 4, lx + 4, ly - 4, fill='#ffffff', width=2, tags='dyn')
        c(lx - 6, ly - 6, lx + 6, ly + 6, fill=SKIN, outline='', tags='dyn')
        # ---- torso, shirt, tie
        self.create_polygon(*rr(tx - 28, sy - 8, tx + 28, fy - 34, 14), smooth=True, fill=C['ac'], outline='#1b5fb5',
                            width=2, tags='dyn')
        self.create_polygon(tx - 9, sy - 8, tx + 9, sy - 8, tx, sy + 18, fill='#ffffff', outline='', tags='dyn')
        self.create_polygon(tx - 3, sy + 2, tx + 3, sy + 2, tx + 4, sy + 26, tx, sy + 32, tx - 4, sy + 26,
                            fill=C['teal'], outline='', tags='dyn')
        # ---- right arm (front)
        rx_, ry_ = self._arm(tx + 24, sy + 4, *P['R'])
        c(rx_ - 6.5, ry_ - 6.5, rx_ + 6.5, ry_ + 6.5, fill=SKIN, outline='', tags='dyn')
        # ---- head
        self.create_rectangle(hx - 6, sy - 16, hx + 6, sy - 6, fill=SKIN, outline='', tags='dyn')
        for sgn in (-1, 1):
            c(hx + sgn * 22 - 4, hy - 5, hx + sgn * 22 + 4, hy + 6, fill=SKIN, outline='', tags='dyn')
        c(hx - 22, hy - 22, hx + 22, hy + 22, fill=SKIN, outline='#d9a982', tags='dyn')
        self.create_arc(hx - 24, hy - 25, hx + 24, hy + 21, start=40, extent=100, fill=HAIR, outline=HAIR,
                        style='chord', tags='dyn')
        face = P['face']
        for sgn in (-1, 1):                                              # cheeks
            if face in ('happy', 'smile', 'wow'):
                c(hx + sgn * 13 - 4, hy + 5, hx + sgn * 13 + 4, hy + 10, fill='#f6b2aa', outline='', tags='dyn')
        look = P.get('look') or (hx + 40, hy)
        lx_, ly_ = look[0] - hx, look[1] - hy
        dl = math.hypot(lx_, ly_) or 1
        px, py = lx_ / dl * 2.6, ly_ / dl * 2.6
        for sgn in (-1, 1):                                              # eyes + round glasses
            ex, ey = hx + sgn * 9, hy - 1
            if face == 'happy':
                c(ex - 8, ey - 8, ex + 8, ey + 8, outline=INK, width=2, tags='dyn')
                self.create_arc(ex - 5, ey - 4, ex + 5, ey + 6, start=20, extent=140, style='arc', outline=INK,
                                width=2, tags='dyn')
            elif P['blink']:
                c(ex - 8, ey - 8, ex + 8, ey + 8, outline=INK, width=2, tags='dyn')
                self.create_line(ex - 5, ey + 1, ex + 5, ey + 1, fill=INK, width=2, tags='dyn')
            else:
                big = 6.5 if face == 'wow' else 5.2
                c(ex - 8.5, ey - 8.5, ex + 8.5, ey + 8.5, fill='#ffffff', outline=INK, width=2, tags='dyn')
                pr = 1.8 if face == 'wow' else 2.6
                c(ex + px - pr, ey + py - pr, ex + px + pr, ey + py + pr, fill=INK, outline='', tags='dyn')
        self.create_line(hx - 1, hy - 1, hx + 1, hy - 1, fill=INK, width=2, tags='dyn')
        if face in ('wow', 'happy'):                                     # eyebrows
            for sgn in (-1, 1):
                self.create_line(hx + sgn * 4, hy - 16, hx + sgn * 14, hy - 16, fill=HAIR, width=2, tags='dyn')
        elif face == 'oops':
            self.create_line(hx - 15, hy - 11, hx - 4, hy - 15, fill=HAIR, width=2, tags='dyn')
            self.create_line(hx + 4, hy - 15, hx + 15, hy - 11, fill=HAIR, width=2, tags='dyn')
        else:
            for sgn in (-1, 1):
                self.create_line(hx + sgn * 4, hy - 13, hx + sgn * 14, hy - 13, fill=HAIR, width=2, tags='dyn')
        if face == 'happy':                                              # mouth
            self.create_arc(hx - 8, hy + 3, hx + 8, hy + 19, start=180, extent=180, fill='#8a2f3c', outline=INK,
                            style='chord', width=2, tags='dyn')
        elif face == 'wow':
            c(hx - 4, hy + 8, hx + 4, hy + 17, fill='#8a2f3c', outline=INK, width=2, tags='dyn')
        elif face == 'oops':
            self.create_arc(hx - 6, hy + 11, hx + 6, hy + 19, start=20, extent=140, style='arc', outline=INK, width=2,
                            tags='dyn')
            c(hx + 20, hy - 12, hx + 26, hy - 3, fill='#8fd0ff', outline='#5aa9e6', tags='dyn')
        elif face == 'focus':
            self.create_line(hx - 5, hy + 12, hx + 5, hy + 12, fill=INK, width=2, tags='dyn')
        else:
            self.create_arc(hx - 7, hy + 3, hx + 7, hy + 14, start=200, extent=140, style='arc', outline=INK, width=2,
                            tags='dyn')
        # ---- graduation cap with a golden tassel
        self.create_polygon(*rr(hx - 15, hy - 29, hx + 15, hy - 18, 4), smooth=True, fill=INK, outline='', tags='dyn')
        self.create_polygon(hx - 32, hy - 29, hx, hy - 41, hx + 32, hy - 29, hx, hy - 17, fill='#2c3650', outline=INK,
                            tags='dyn')
        self.create_line(hx, hy - 29, hx + 26, hy - 26, hx + 26, hy - 12, fill=GOLD, width=2, tags='dyn')
        c(hx + 23, hy - 13, hx + 29, hy - 4, fill=GOLD, outline='', tags='dyn')
        # ---- landing ring, sparkles, moving coin, speech bubble
        if P.get('ring'):
            x, y, u = P['ring']
            c(x - self.rx * (1 + u * .8), y - self.ry * (1 + u * .8), x + self.rx * (1 + u * .8),
              y + self.ry * (1 + u * .8), outline=mix(C['ok'], C['bg2'], u), width=3, tags='dyn')
        self.sparks = [s for s in self.sparks if now - s['t0'] < .6]
        for s in self.sparks:
            u = (now - s['t0']) / .6
            self._star(s['x'] + s['vx'] * u, s['y'] + s['vy'] * u, 9 * math.sin(math.pi * u) + 1, GOLD)
        if P['coin'] and P['coin'][4] > .05:
            x, y, sym, nt, s, fl, top = P['coin']
            self._coin(x, y, sym, nt, 'dyn', s=s, fl=fl, top=top)
        if P['bub']:
            self._bubble(P['bub'], hx, hy)

    def _bubble(self, text, hx, hy):
        w, h = self.bf.measure(text) + 26, 28
        x1 = max(6, min(self.W - w - 6, self.tx - w / 2))
        y2 = self.sy - 82
        y1 = y2 - h
        self.create_polygon(*rr(x1 + 1, y1 + 3, x1 + w + 1, y2 + 3, 12), smooth=True, fill=mix(C['bg2'], '#8a93ad', .25),
                            outline='', tags='dyn')
        self.create_polygon(*rr(x1, y1, x1 + w, y2, 12), smooth=True, fill='#ffffff', outline=C['nd'], tags='dyn')
        self.create_polygon(hx - 6, y2 - 1, hx + 6, y2 - 1, hx, y2 + 10, fill='#ffffff', outline='', tags='dyn')
        self.create_line(hx - 6, y2, hx, y2 + 10, hx + 6, y2, fill=C['nd'], tags='dyn')
        self.create_line(hx - 5, y2, hx + 5, y2, fill='#ffffff', width=2, tags='dyn')
        self.create_text(x1 + w / 2, (y1 + y2) / 2, text=text, font=self.bf, fill=C['tx'], tags='dyn')


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
