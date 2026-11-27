"""The six tools of Parsera. Every tab is independent: it has its own grammar and its own input."""
import tkinter as tk
from tkinter import messagebox

from core import (parse_grammar, tokenize, parse_all, fresh, derivation_frames, detect, gen, infer, unamb,
                  grammar_text, ast_frames, tok_expr, conv, opp, rel)
from ui_common import (C, UI, MONO, Page, card, lbl, txt, entry, btn, combo, set_text, TreeCanvas, StackView,
                       ChipRow, Player, StepBar, Rounded, mix)

WARN = '#d97706'

def leaf_nodes(n):
    """Leaf nodes of a (partly expanded) tree, left to right."""
    return [x for c in n.k for x in leaf_nodes(c)] if n.k else [n]


def pair(a, b=None):
    """Derivation frames for one tree, or two trees stepped together."""
    fa = derivation_frames(a)
    fb = derivation_frames(b) if b is not None else None
    n = max(len(fa), len(fb or []))
    return [dict(a=fa[min(k, len(fa) - 1)], b=fb[min(k, len(fb) - 1)] if fb else None) for k in range(n)]


class Tab(Page):
    ran = False

    def __init__(self, m, sh=None):
        super().__init__(m)
        self.b = self.body

    def safe(self, f):
        try:
            f()
        except Exception as e:  # show any grammar / input error to the user
            messagebox.showerror('Error', str(e))

    def on_show(self):
        if not self.ran:
            self.ran = True
            self.safe(self.run)

    def sec(self, c, n, title):
        """Numbered section heading inside a card."""
        f = tk.Frame(c, bg=C['p'])
        f.pack(fill='x', pady=(0, 12))
        dot = tk.Canvas(f, width=28, height=28, bg=C['p'], highlightthickness=0)
        dot.create_oval(1, 1, 27, 27, fill=C['ac'], outline='')
        dot.create_text(14, 14, text=str(n), fill='#ffffff', font=(UI[0], 11, 'bold'))
        dot.pack(side='left')
        tk.Label(f, text=title, bg=C['p'], fg=C['tx'], font=(UI[0], 13, 'bold')).pack(side='left', padx=10)

    def head(self, title, hint=''):
        """Page title and hint on the page itself, then card 1 (the input card)."""
        t = tk.Frame(self.b, bg=C['bg'])
        t.pack(fill='x', pady=(2, 14))
        tk.Label(t, text=title, bg=C['bg'], fg=C['tx'], font=(UI[0], 22, 'bold'), anchor='w').pack(fill='x')
        if hint:
            tk.Label(t, text=hint, bg=C['bg'], fg=C['mu'], font=UI, anchor='w', justify='left',
                     wraplength=860).pack(fill='x', pady=(4, 0))
        c = card(self.b)
        c.pack(fill='x', pady=(0, 18))
        self.sec(c, 1, 'Enter your input')
        return c

    def row(self, c):
        r = tk.Frame(c, bg=C['p'])
        r.pack(fill='x', pady=(14, 4))
        return r

    def out_card(self, title='Watch it work'):
        """Card 2: the animated result."""
        c = card(self.b)
        c.pack(fill='x', pady=(0, 10))
        self.sec(c, 2, title)
        return c

    def dock_player(self, render):
        """Player controls live in a fixed rounded bar at the bottom of the tab, so they are always visible."""
        bar = Rounded(self.dock, C['p'], '', pad=10, r=22, shadow=True)
        bar.pack(fill='x', padx=2, pady=(8, 2))
        pl = Player(bar.inner, render)
        pl.pack(fill='x')
        return pl

    def field_label(self, c, text):
        lbl(c, text, mu=True, bold=True, size=10).pack(fill='x', pady=(12, 5))

    # ---- own grammar + own input box; the action row comes last, below the fields
    def gbox(self, c, initial_grammar, initial_input,
             string_label='Input string (symbols separated by spaces)'):
        self.field_label(c, 'Grammar   (one rule per line, | for alternatives)')
        self.g = txt(c, 5)
        self.g.pack(fill='x')
        self.g.insert('1.0', initial_grammar)
        self.field_label(c, string_label)
        self.st = entry(c)
        self.st.pack(fill='x')
        self.st.insert(0, initial_input)
        return self.row(c)

    def grammar(self):
        return parse_grammar(self.g.get('1.0', 'end'))

    def say(self, text, col):
        """Result banner: tinted strip in the colour of the verdict (red / amber / green)."""
        self.v.config(text=text, fg=col, bg=mix(col, '#ffffff', .88), padx=14, pady=9, wraplength=820)
        self.v.pack_configure(pady=(14, 0))

    # ---- one or two animated trees
    def mk_trees(self, o, h=240):
        f = tk.Frame(o, bg=C['p'])
        f.pack(fill='x', pady=4)
        self.tf = f
        self.la = lbl(f, 'Parse tree', bold=True, size=12)
        self.la.grid(row=0, column=0, sticky='w', padx=4)
        self.lb = lbl(f, 'Parse tree 2', bold=True, size=12)
        self.lb.grid(row=0, column=1, sticky='w', padx=4)
        cap = 'Current string (derivation)'
        self.ra, self.rb = ChipRow(f, 300, cap=cap), ChipRow(f, 300, cap=cap)
        self.ra.grid(row=1, column=0, sticky='ew', padx=4, pady=(0, 4))
        self.rb.grid(row=1, column=1, sticky='ew', padx=4, pady=(0, 4))
        self.ta, self.tb = TreeCanvas(f, h, legend=True), TreeCanvas(f, h)
        self.ta.grid(row=2, column=0, sticky='nsew', padx=4)
        self.tb.grid(row=2, column=1, sticky='nsew', padx=4)
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

    def show_two(self, two):
        if two:
            self.lb.grid()
            self.rb.grid()
            self.tb.grid()
            self.la.config(text='Parse tree 1')
        else:
            self.lb.grid_remove()
            self.rb.grid_remove()
            self.tb.grid_remove()
            self.la.config(text='Parse tree')
        self.tf.columnconfigure(1, weight=1 if two else 0)

    def clear(self):
        self.pl.load([])
        self.ta.draw([])
        self.tb.draw([])
        self.ra.show([])
        self.rb.show([])
        self.x.config(text='')

    @staticmethod
    def ribbon(row, fr):
        """Show the current derivation string; symbols just produced by the last expansion are blue,
        non-terminals still to expand have a blue outline."""
        nodes = [n for n in leaf_nodes(fr['root']) if n.l != 'ε']
        new = fr['hl'] or ()
        row.show([n.l for n in nodes], kinds=['new' if n.id in new else 't' if n.t else 'nt' for n in nodes])

    def render_pair(self, f):
        self.ta.draw([f['a']['root']], f['a']['hl'])
        self.ribbon(self.ra, f['a'])
        if f['b']:
            self.tb.draw([f['b']['root']], f['b']['hl'])
            self.ribbon(self.rb, f['b'])
            self.x.config(text='Tree 1: ' + f['a']['txt'] + '   |   Tree 2: ' + f['b']['txt'])
        else:
            self.x.config(text=f['a']['txt'])


# ------------------------------------------------------------------ 1. grammar -> parse tree
class Tab1(Tab):
    def __init__(self, m, sh=None):
        super().__init__(m, sh)
        c = self.head('Grammar → Parse Tree',
                      'Grammar: one rule per line, symbols separated by spaces, | for alternatives, ε for empty. '
                      'The first line’s left-hand side is the start symbol.')
        r = self.gbox(c, 'E -> E + E | E * E | ( E ) | id', 'id + id * id')
        btn(r, 'Parse and animate', lambda: self.safe(self.run), True).pack(side='left', padx=8)
        self.v = lbl(c, bold=True, size=11)
        self.v.pack(fill='x')
        o = self.out_card()
        self.x = StepBar(o)
        self.x.pack(fill='x', pady=(0, 10))
        self.mk_trees(o)
        self.pl = self.dock_player(self.render_pair)

    def run(self):
        g = self.grammar()
        t = parse_all(g, tokenize(g, self.st.get()), 2)
        if not t:
            self.say('This string cannot be derived from the grammar.', C['er'])
            self.clear()
            return
        w = detect(g, 9 if 'else' in g.TT else 7)[0]
        a, b = fresh(t[0]), (fresh(t[1]) if len(t) > 1 else None)
        if b is not None:
            self.say('This is AMBIGUOUS: this input has more than one parse tree. Both trees are shown below.', C['er'])
        elif w is not None:
            self.say(f"This grammar is AMBIGUOUS (for example '{' '.join(w)}' has two parse trees), "
                     f"but this input has only one parse tree.", WARN)
        else:
            self.say('Unambiguous: this input has exactly one parse tree.', C['ok'])
        self.show_two(b is not None)
        self.pl.load(pair(a, b), True)


# ------------------------------------------------------------------ 2. ambiguity detection
class Tab2(Tab):
    def __init__(self, m, sh=None):
        super().__init__(m, sh)
        c = self.head('Ambiguity Detect',
                      'Enter a grammar and optionally a sentence. If the sentence has multiple parse trees, '
                      'they are shown; otherwise, the tool searches generated sentences for ambiguity.')
        r = self.gbox(c, 'E -> E + E | E * E | ( E ) | id', 'id + id * id',
                      'Input string (optional)')
        lbl(r, 'Max length').pack(side='left', padx=(12, 0))
        self.L = tk.StringVar(value='7')
        entry(r, 5, textvariable=self.L).pack(side='left', padx=6)
        btn(r, 'Detect ambiguity', lambda: self.safe(self.run), True).pack(side='left', padx=8)
        self.v = lbl(c, bold=True, size=11)
        self.v.pack(fill='x')
        o = self.out_card()
        self.x = StepBar(o)
        self.x.pack(fill='x', pady=(0, 10))
        self.mk_trees(o)
        self.pl = self.dock_player(self.render_pair)

    def run(self):
        g = self.grammar()
        L = int(self.L.get())
        s = self.st.get().strip()
        w = t = None
        if s:
            tk_ = tokenize(g, s)
            tt = parse_all(g, tk_, 2)
            if len(tt) > 1:
                w, t = tk_, tt
        G = None
        if t is None:
            w, t, G = detect(g, L)
        if w is None:
            self.say(f"No ambiguity found in {len(G[0])} sentences up to length {L}"
                     f"{' (search capped)' if G[1] else ''}. This is not a proof of unambiguity.", C['ok'])
            self.show_two(False)
            self.clear()
            return
        self.say(f"This is AMBIGUOUS: the sentence '{' '.join(w)}' has two different parse trees.", C['er'])
        self.show_two(True)
        self.pl.load(pair(fresh(t[0]), fresh(t[1])), True)


# ------------------------------------------------------------------ 3. make unambiguous
class Tab3(Tab):
    def __init__(self, m, sh=None):
        super().__init__(m, sh)
        c = self.head('Make Unambiguous',
                      'Operator rules are split into precedence and associativity levels; dangling else rules are '
                      'split into matched and unmatched forms. Precedence goes low to high; use | between levels '
                      'and :R for right associativity.')
        r2 = self.gbox(c, 'E -> E + E | E * E | ( E ) | id', 'id + id * id',
                       'Input string (optional, empty = use the ambiguous sentence found)')
        lbl(r2, 'Precedence').pack(side='left')
        self.pt = entry(r2, 26)
        self.pt.pack(side='left', padx=6)
        lbl(r2, 'Max length').pack(side='left', padx=(12, 0))
        self.L = tk.StringVar(value='7')
        entry(r2, 5, textvariable=self.L).pack(side='left', padx=6)
        btn(r2, 'Make unambiguous', lambda: self.safe(self.run), True).pack(side='left', padx=8)
        self.v = lbl(c, bold=True, size=11)
        self.v.pack(fill='x')
        self.v2 = lbl(c, bold=True, size=11)
        self.v2.pack(fill='x')
        self.field_label(c, 'New grammar (result)')
        self.o = txt(c, 7)
        self.o.pack(fill='x')
        o = self.out_card()
        self.x = StepBar(o)
        self.x.pack(fill='x', pady=(0, 10))
        self.mk_trees(o)
        self.pl = self.dock_player(self.render_pair)

    def run(self):
        g = self.grammar()
        L = int(self.L.get())
        if not self.pt.get().strip():
            self.pt.insert(0, infer(g))
        new, changed = unamb(g, self.pt.get())
        w, _, G = detect(g, L)
        s = self.st.get().strip()
        tk_ = tokenize(g, s) if s else w
        self.v2.config(text='')
        if not changed:
            set_text(self.o, grammar_text(g.P))
            if w is not None:
                self.say('Ambiguous, but no supported pattern (operator rules or dangling else) found, so no rewrite.', C['er'])
                self.show_two(False)
                self.clear()
                return
            self.say('This grammar is already unambiguous, no rewrite needed.', C['ok'])
            ng = g
        else:
            ng = parse_grammar(new)
            B = gen(ng, L)
            same = G[0] == B[0]
            w2 = detect(ng, L)[0]
            set_text(self.o, new)
            self.say(f"{'✓ Same language' if same else '✗ Languages differ'}: {len(G[0])} sentences (original) "
                     f"vs {len(B[0])} (new), up to length {L}.", C['ok'] if same else C['er'])
            self.v2.config(text='✗ Still ambiguous' if w2 else '✓ No ambiguity found in the new grammar.',
                           fg=C['er'] if w2 else C['ok'])
        if not tk_:
            self.show_two(False)
            self.clear()
            return
        t = parse_all(ng, tk_, 2)
        if not t:
            self.v2.config(text='This input cannot be derived from the new grammar.', fg=C['er'])
            self.show_two(False)
            self.clear()
            return
        self.show_two(len(t) > 1)
        self.pl.load(pair(fresh(t[0]), fresh(t[1]) if len(t) > 1 else None), True)


# ------------------------------------------------------------------ 4. parse tree -> AST
class Tab4(Tab):
    def __init__(self, m, sh=None):
        super().__init__(m, sh)
        c = self.head('Parse Tree → AST',
                      'Enter a grammar and input. The parse tree is simplified by removing brackets and '
                      'single-child chains, with operators promoted to parents.')
        r = self.gbox(c, 'E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id',
                      'id + id * id')
        btn(r, 'Build tree and convert to AST', lambda: self.safe(self.run), True).pack(side='left', padx=8)
        self.v = lbl(c, bold=True, size=11)
        self.v.pack(fill='x')
        o = self.out_card()
        self.x = StepBar(o)
        self.x.pack(fill='x', pady=(0, 10))
        self.tree = TreeCanvas(o, 300)
        self.tree.pack(fill='x', pady=6)
        self.pl = self.dock_player(self.render)

    def run(self):
        g = self.grammar()
        t = parse_all(g, tokenize(g, self.st.get()), 2)
        if not t:
            self.say('This string cannot be derived from the grammar.', C['er'])
            self.pl.load([])
            self.tree.draw([])
            self.x.config(text='')
            return
        if len(t) > 1:
            self.say('This input is ambiguous, so the first parse tree is converted.', WARN)
        else:
            self.say('Parse tree built; converting it to an AST.', C['ok'])
        self.pl.load(ast_frames(fresh(t[0])), True)

    def render(self, f):
        self.tree.draw([f['root']])
        self.x.config(text=f['txt'])


# ------------------------------------------------------------------ 5. infix -> prefix / postfix
class Tab5(Tab):
    def __init__(self, m, sh=None):
        super().__init__(m, sh)
        c = self.head('Infix → Prefix / Postfix',
                      'Enter an expression to see each conversion step with the operator stack.')
        r = self.row(c)
        self.e = entry(r, 30)
        self.e.insert(0, 'a + b * ( c - d ) ^ 2')
        self.e.pack(side='left')
        self.mode = combo(r, ['Postfix', 'Prefix'], 10)
        self.mode.current(0)
        self.mode.pack(side='left', padx=8)
        self.mode.bind('<<ComboboxSelected>>', lambda e: self.safe(self.run))
        btn(r, 'Convert and animate', lambda: self.safe(self.run), True).pack(side='left')
        o = self.out_card()
        self.tape = ChipRow(o, 700, cap='Input tokens (left to right)')
        self.tape.pack(fill='x', pady=4)
        two = tk.Frame(o, bg=C['p'])
        two.pack(fill='x')
        lbl(two, 'Operator stack', bold=True).grid(row=0, column=0, sticky='w')
        self.olbl = lbl(two, 'Output (postfix)', bold=True)
        self.olbl.grid(row=0, column=1, sticky='w', padx=14)
        self.stack = StackView(two, 250, 300)
        self.stack.grid(row=1, column=0, sticky='n')
        self.out = ChipRow(two, 520, tray=True, colored=True)
        self.out.grid(row=1, column=1, sticky='nwe', padx=14)
        two.columnconfigure(1, weight=1)
        self.x = StepBar(o)
        self.x.pack(fill='x', pady=(10, 10))
        self.pl = self.dock_player(self.render)

    def run(self):
        tk_ = tok_expr(self.e.get())
        if not tk_:
            raise ValueError('Enter an expression')
        self.olbl.config(text='Output (postfix)' if self.mode.current() == 0 else 'Output (prefix)')
        self.pl.load(conv(tk_, 'post' if self.mode.current() == 0 else 'pre'), True)

    def render(self, f):
        self.tape.show(f['tk'], on=f['tok'], dn=f['tok'])
        self.stack.show(f['st'], new=f['nSt'])
        self.out.show(f['out'], new=f['nOut'])
        self.x.config(text=f['txt'])


# ------------------------------------------------------------------ 6. operator precedence parser
SY = ['+', '-', '*', '/', '^', 'id', '(', ')', '$']
SYM = {'<': '⋖', '>': '⋗', '=': '≐', 'acc': '✓', 'x': ''}


class Tab6(Tab):
    def __init__(self, m, sh=None):
        super().__init__(m, sh)
        c = self.head('Operator Precedence Parser',
                      'Enter an expression to parse with the built-in operator-precedence rules. '
                      'The table highlights the current precedence relation.')
        r = self.gbox(c, 'E -> E + T | T\nT -> T * F | F\nF -> ( E ) | id',
                      'a + b * ( c - d ) ^ 2', 'Expression string')
        btn(r, 'Parse and animate', lambda: self.safe(self.run), True).pack(side='left', padx=8)
        self.v = lbl(c, bold=True, size=11)
        self.v.pack(fill='x')
        tb = tk.Frame(c, bg=C['p'])
        tb.pack(anchor='w')
        self.cells = {}
        for j, b in enumerate(SY):
            tk.Label(tb, text=b, bg=C['p'], fg=C['mu'], font=MONO, width=4).grid(row=0, column=j + 1)
        for i, a in enumerate(SY):
            tk.Label(tb, text=a, bg=C['p'], fg=C['mu'], font=MONO, width=4).grid(row=i + 1, column=0)
            for j, b in enumerate(SY):
                cell = tk.Label(tb, text=SYM[rel(a, b)], bg=C['p'], fg=C['tx'], font=MONO, width=4,
                                highlightthickness=1, highlightbackground=C['ln'])
                cell.grid(row=i + 1, column=j + 1)
                self.cells[(a, b)] = cell
        o = self.out_card()
        self.tape = ChipRow(o, 700, cap='Input tokens (left to right)')
        self.tape.pack(fill='x', pady=4)
        two = tk.Frame(o, bg=C['p'])
        two.pack(fill='x')
        lbl(two, 'Stack', bold=True).grid(row=0, column=0, sticky='w')
        lbl(two, 'Parse tree being built', bold=True).grid(row=0, column=1, sticky='w', padx=14)
        self.stack = StackView(two, 250, 300)
        self.stack.grid(row=1, column=0, sticky='n')
        self.tree = TreeCanvas(two, 280, legend=True)
        self.tree.grid(row=1, column=1, sticky='nsew', padx=14)
        two.columnconfigure(1, weight=1)
        self.x = StepBar(o)
        self.x.pack(fill='x', pady=(10, 10))
        self.pl = self.dock_player(self.render)

    def run(self):
        self.grammar()
        tk_ = tok_expr(self.st.get())
        if not tk_:
            raise ValueError('Enter an expression')
        self.say('Using built-in operator-precedence rules.', C['ok'])
        self.pl.load(opp(tk_), True)

    def render(self, f):
        self.tape.show(f['T'], on=None if f['er'] else f['i'], dn=f['i'])
        st = f['st']
        top = next((j for j in range(len(st) - 1, -1, -1) if not st[j]['nt']), None)
        self.stack.show([x['s'] for x in st], new=f['r'] in ('<', '=', '>'),
                        nts={j for j, x in enumerate(st) if x['nt']}, top=top)
        for k, cell in self.cells.items():
            on = k == (f['a'], f['b'])
            cell.config(bg=C['ac'] if on else C['p'], fg='#ffffff' if on else C['tx'])
        self.tree.draw(f['roots'], {f['hl']} if f['hl'] else None)
        self.x.config(text=f['txt'], fg=C['er'] if f['er'] else C['tx'])
