"""Parsera core: grammar parsing, ambiguity, rewriting, AST, infix conversion, operator precedence.
Pure logic, no GUI, so it can be tested on its own."""
import re
import time
from itertools import count

_ids = count(1)


class Node:
    def __init__(self, l, t=False, k=None, id=None):
        self.id = id if id is not None else next(_ids)
        self.l, self.t = l, t
        self.k = k if k is not None else []

    def but(self, **kw):
        return Node(kw.get('l', self.l), kw.get('t', self.t), kw.get('k', self.k), self.id)


def fresh(n):
    return Node(n.l, n.t, [fresh(c) for c in n.k])


# ---------------------------------------------------------------- grammar
class Grammar:
    def __init__(self, P, order):
        seen, uniq = set(), []
        for l, r in P:  # a rule written twice is one rule
            if (l, tuple(r)) not in seen:
                seen.add((l, tuple(r)))
                uniq.append((l, r))
        self.P, self.order = uniq, order
        self.NT = set(order)
        self.TT = {s for _, r in P for s in r if s not in self.NT}
        self.start = order[0]
        self.by = {}
        for l, r in self.P:
            self.by.setdefault(l, []).append(r)


def parse_grammar(txt):
    P, order = [], []
    for line in txt.splitlines():
        line = line.strip()
        if not line or line[0] == '#':
            continue
        m = re.match(r'^(\S+?)\s*(?:->|→|::=)\s*(.*)$', line)
        if not m:
            raise ValueError('Bad rule: ' + line)
        if m[1] not in order:
            order.append(m[1])
        for alt in m[2].split('|'):
            r = alt.split()
            if len(r) == 1 and r[0] in ('ε', 'eps', 'epsilon', 'λ'):
                r = []
            P.append((m[1], r))
    if not P:
        raise ValueError('Grammar is empty')
    return Grammar(P, order)


def grammar_text(rows):
    o, m = [], {}
    for l, r in rows:
        if l not in m:
            m[l] = []
            o.append(l)
        m[l].append(' '.join(r) if r else 'ε')
    return '\n'.join(f"{l} -> {' | '.join(m[l])}" for l in o)


def tmatch(g, s, t):
    return (s == t
            or (s == 'id' and t not in g.TT and re.match(r'[A-Za-z_]\w*$|\d', t) is not None)
            or (s == 'num' and re.match(r'\d', t) is not None))


def tokenize(g, s):
    s = s.strip()
    if re.search(r'\s', s):
        return s.split()
    T = sorted((x for x in g.TT if x not in ('id', 'num')), key=len, reverse=True)
    out, i = [], 0
    while i < len(s):
        t = next((x for x in T if s.startswith(x, i)), None)
        if t:
            out.append(t)
            i += len(t)
            continue
        m = re.match(r'\d+(\.\d+)?|[A-Za-z_]\w*|\S', s[i:])
        out.append(m[0])
        i += len(m[0])
    return out


def count_trees(g, tk, cap=2):
    """Number of parse trees of tk, capped at `cap`. Handles left recursion, epsilon and unit cycles
    (a cycle such as A -> A gives infinitely many trees, which shows up as `cap`)."""
    n, cnt = len(tk), {}
    for length in range(n + 1):
        for i in range(n - length + 1):
            j = i + length
            while True:
                memo, tot = {}, {}

                def ways(ri, x, p, q):
                    r = g.P[ri][1]
                    if x == len(r):
                        return 1 if p == q else 0
                    key = (ri, x, p, q)
                    if key in memo:
                        return memo[key]
                    s, res = r[x], 0
                    if s not in g.NT:
                        if p < q and tmatch(g, s, tk[p]):
                            res = ways(ri, x + 1, p + 1, q)
                    else:
                        for m in range(p, q + 1):
                            c = cnt.get((s, p, m), 0)
                            if c:
                                res = min(cap, res + c * ways(ri, x + 1, m, q))
                                if res >= cap:
                                    break
                    memo[key] = res
                    return res

                for ri, (A, r) in enumerate(g.P):
                    tot[A] = min(cap, tot.get(A, 0) + ways(ri, 0, i, j))
                ch = False
                for A, v in tot.items():
                    if v > cnt.get((A, i, j), 0):
                        cnt[(A, i, j)] = v
                        ch = True
                if not ch:
                    break
    return cnt.get((g.start, 0, n), 0)


def parse_all(g, tk, cap=2):
    """Return up to `cap` structurally different parse trees of token list tk (any CFG)."""
    n, chart, seen = len(tk), {}, {}

    def leaf(l):
        x = Node(l, True)
        x.sg = 't:' + l
        return x

    def combos(r, x, i, j):
        if x == len(r):
            return [[]] if i == j else []
        s = r[x]
        if s not in g.NT:
            if i < j and tmatch(g, s, tk[i]):
                return [[leaf(tk[i])] + rest for rest in combos(r, x + 1, i + 1, j)][:cap]
            return []
        out = []
        for m in range(i, j + 1):
            for a in chart.get((s, i, m), []):
                for rest in combos(r, x + 1, m, j):
                    out.append([a] + rest)
                    if len(out) >= cap:
                        return out
        return out

    for length in range(n + 1):
        for i in range(n - length + 1):
            j = i + length
            while True:
                ch = False
                for A, r in g.P:
                    key = (A, i, j)
                    lst = chart.setdefault(key, [])
                    sg = seen.setdefault(key, set())
                    if len(lst) >= cap:
                        continue
                    for ks in combos(r, 0, i, j):
                        if not ks:
                            e = Node('ε', True)
                            e.sg = 'e'
                            ks = [e]
                        node = Node(A, False, ks)
                        node.sg = A + '(' + ','.join(k.sg for k in ks) + ')'
                        if node.sg in sg:
                            continue
                        sg.add(node.sg)
                        lst.append(node)
                        ch = True
                        if len(lst) >= cap:
                            break
                if not ch:
                    break
    return chart.get((g.start, 0, n), [])


# ---------------------------------------------------------------- ambiguity
def gen(g, L, cap=30000):
    """All sentences (as strings of space separated tokens) of length <= L, exact for any CFG.
    Returns (sorted sentence list, capped flag)."""
    lang, capped, ch = {A: set() for A in g.NT}, False, True
    while ch:
        ch = False
        for A, r in g.P:
            cur = {()}
            for s in r:
                S = lang[s] if s in g.NT else {(s,)}
                nxt = set()
                for p in cur:
                    for q in S:
                        if len(p) + len(q) <= L:
                            nxt.add(p + q)
                    if len(nxt) > cap:
                        capped = True
                        break
                cur = nxt
                if not cur:
                    break
            for w in cur:
                if w not in lang[A]:
                    if len(lang[A]) >= cap:
                        capped = True
                        break
                    lang[A].add(w)
                    ch = True
    return sorted((' '.join(w) for w in lang[g.start]), key=lambda s: (len(s.split()), s)), capped


def detect(g, L, budget=8.0):
    """Look for a sentence with two different parse trees.
    Returns (witness_tokens, trees, (sentences, incomplete)); witness is None if nothing was found.
    incomplete = True when the sentence set was capped or the time budget ran out."""
    sents, capped = gen(g, L)
    t0 = time.time()
    for s in sents:
        if time.time() - t0 > budget:
            return None, None, (sents, True)
        tk = s.split()
        if count_trees(g, tk) > 1:
            return tk, parse_all(g, tk, 2), (sents, capped)
    return None, None, (sents, capped)


DP = {'+': (1, 0), '-': (1, 0), '*': (2, 0), '/': (2, 0), '%': (2, 0), '^': (3, 1), '**': (3, 1)}
PR = {k: v for k, v in DP.items() if k != '**'}


def _is_bin(g, A, r):
    return ((len(r) == 3 and r[0] == A and r[2] == A and r[1] not in g.NT)
            or (len(r) == 2 and r[0] == A and r[1] == A))


def infer(g):
    ops = []
    for l, r in g.P:
        if len(r) == 3 and r[0] == l and r[2] == l and r[1] not in g.NT:
            ops.append(r[1])
        elif len(r) == 2 and r[0] == l and r[1] == l:
            ops.append('cat')
    u = list(dict.fromkeys(ops))
    lv = {}
    for o in u:
        k = DP[o][0] if o in DP else 50 + u.index(o)
        lv.setdefault(k, []).append(o + (':R' if o in DP and DP[o][1] else ''))
    return ' | '.join(' '.join(lv[k]) for k in sorted(lv))


def unamb(g, pt):
    """Rewrite operator rules into precedence layers and dangling-else into matched/unmatched.
    pt = precedence text, low to high, levels split by '|', ':R' marks right associative."""
    names = set(g.NT)

    def nn(b):
        c, i = b, 1
        while c in names:
            c = b + str(i)
            i += 1
        names.add(c)
        return c

    lv = []
    for part in pt.split('|'):
        l = [(o[:-2], 1) if o.endswith(':R') else (o, 0) for o in part.split()]
        if l:
            lv.append(l)
    R, ch = [], False
    for A in g.order:
        mine = [r for l, r in g.P if l == A]
        if any(_is_bin(g, A, r) for r in mine):
            ch = True
            used = list(dict.fromkeys(r[1] if len(r) == 3 else 'cat' for r in mine if _is_bin(g, A, r)))
            L = [[x for x in l if x[0] in used] for l in lv]
            L = [l for l in L if l]
            for o in used:
                if not any(x[0] == o for l in L for x in l):
                    L.append([(o, 0)])
            n = len(L)
            nm = [A] + [nn(['T', 'F', 'G', 'H'][i - 1] if i <= 4 else 'Q') for i in range(1, n)] + [nn('P')]
            for i, l in enumerate(L):
                rt = l[0][1]
                for o, _ in l:
                    c = [] if o == 'cat' else [o]
                    R.append((nm[i], [nm[i + 1]] + c + [nm[i]] if rt else [nm[i]] + c + [nm[i + 1]]))
                R.append((nm[i], [nm[i + 1]]))
            for r in mine:
                if _is_bin(g, A, r):
                    continue
                un = len(r) == 2 and r[1] == A and r[0] not in g.NT
                R.append((nm[n], [r[0], nm[n]] if un else [nm[0] if s == A else s for s in r]))
        else:
            p1 = next((p for p in mine if len(p) > 1 and p[-1] == A and any(
                len(q) == len(p) + 2 and q[len(p)] == 'else' and q[-1] == A and q[:len(p)] == p for q in mine)), None)
            if p1 is None:
                R += [(A, r) for r in mine]
                continue
            ch = True
            k, pf, M, Uu = len(p1), p1[:-1], nn('M'), nn('U')
            R += [(A, [M]), (A, [Uu]), (M, pf + [M, 'else', M])]
            for p in mine:
                if p is p1 or (len(p) == k + 2 and p[k] == 'else' and p[:k] == p1):
                    continue
                R.append((M, p))
            R += [(Uu, pf + [A]), (Uu, pf + [M, 'else', Uu])]
    return grammar_text(R), ch


# ---------------------------------------------------------------- tree frames
def nts(root):
    out = []

    def f(n):
        if not n.t and n.k:
            out.append(n)
            for c in n.k:
                f(c)
    f(root)
    return out


def prune(n, ex):
    return n.but(k=[prune(c, ex) for c in n.k]) if n.id in ex else n.but(k=[])


def leaves(n):
    if n.k:
        return [x for c in n.k for x in leaves(c)]
    return [] if n.l == 'ε' else [n.l]


def derivation_frames(root):
    """One frame per non-terminal expansion (leftmost order), like a derivation."""
    N, F = nts(root), []
    for k in range(len(N) + 1):
        ex = {x.id for x in N[:k]}
        r = prune(root, ex)
        c = N[k - 1] if k else None
        F.append(dict(root=r, hl={c.id, *[x.id for x in c.k]} if c else None,
                      txt=f"Expand {c.l} → {' '.join(x.l for x in c.k)}" if c else f"Start symbol {root.l}",
                      form=leaves(r)))
    return F


def _is_p(n):
    return n.t and n.l in ('(', ')', 'ε')


def _is_op(l):
    return re.fullmatch(r'[^\w\s()]+', l) is not None


def no_paren(n):
    return n.but(k=[no_paren(c) for c in n.k if not _is_p(c)])


def collapse(n):
    k = [collapse(c) for c in n.k]
    return k[0] if (not n.t and len(k) == 1) else n.but(k=k)


def lift(n):
    k = [lift(c) for c in n.k]
    if not n.t and len(k) == 3 and k[1].t and not k[1].k and _is_op(k[1].l):
        return k[1].but(k=[k[0], k[2]])
    if not n.t and len(k) == 2 and k[0].t and not k[0].k and _is_op(k[0].l):
        return k[0].but(k=[k[1]])
    return n.but(k=k)


def sig(n):
    return f"{n.id}{n.l}({','.join(map(sig, n.k))})"


def preorder(n):
    return [n.l] + [x for c in n.k for x in preorder(c)]


def postorder(n):
    return [x for c in n.k for x in postorder(c)] + [n.l]


def ast_frames(root):
    t = root
    F = [dict(root=t, txt='Original parse tree')]
    P = [('Remove brackets ( ) and ε', no_paren), ('Collapse single-child chains', collapse),
         ('Lift operator above its operands', lift)]
    for _ in range(6):
        changed = False
        for nm, f in P:
            x = f(t)
            if sig(x) != sig(t):
                t, changed = x, True
                F.append(dict(root=t, txt=nm))
        if not changed:
            break
    F[-1]['txt'] += f" — final AST.  Prefix: {' '.join(preorder(t))}  |  Postfix: {' '.join(postorder(t))}"
    return F


# ---------------------------------------------------------------- infix -> prefix / postfix
def tok_expr(s):
    return re.findall(r'\d+(?:\.\d+)?|[A-Za-z_]\w*|\S', s)


def check_expr(tk):
    """Raise ValueError with a clear message for an invalid infix expression."""
    prev, depth = 'op', 0
    for t in tk:
        if t == '(':
            if prev == 'operand':
                raise ValueError("Missing operator before '('")
            depth += 1
            prev = 'op'
        elif t == ')':
            if prev == 'op':
                raise ValueError("Missing operand before ')'")
            depth -= 1
            if depth < 0:
                raise ValueError("Unbalanced brackets: extra ')'")
            prev = 'operand'
        elif t in PR:
            if prev == 'op':
                raise ValueError(f"Missing operand before '{t}' (unary operators are not supported)")
            prev = 'op'
        elif re.fullmatch(r'[A-Za-z_]\w*|\d+(\.\d+)?', t):
            if prev == 'operand':
                raise ValueError(f"Missing operator before '{t}'")
            prev = 'operand'
        else:
            raise ValueError(f"Unknown token '{t}' (allowed: names, numbers, + - * / % ^ and brackets)")
    if prev == 'op':
        raise ValueError('The expression is empty or ends with an operator')
    if depth:
        raise ValueError("Unbalanced brackets: missing ')'")


def conv(tk, mode):
    """Shunting-yard with animation frames. mode: 'post' or 'pre' (pre = reverse, swap brackets, reverse output)."""
    check_expr(tk)
    T = list(tk)
    if mode == 'pre':
        T = [')' if t == '(' else '(' if t == ')' else t for t in reversed(T)]
    st, out, fr = [], [], []

    def sn(txt, i, nst=False, nout=False):
        fr.append(dict(tk=T, tok=i, txt=txt, st=list(st), out=list(out), nSt=nst, nOut=nout))

    sn('Start: stack and output are empty' + (' (expression reversed, brackets swapped)' if mode == 'pre' else ''), -1)
    for i, t in enumerate(T):
        if t in PR:
            p, r = PR[t]
            while st and st[-1] in PR:
                s = st[-1]
                q = PR[s][0]
                if q > p or (q == p and (not r if mode == 'post' else r)):
                    out.append(st.pop())
                    sn(f'{s} binds at least as tight as {t} → pop {s} to output', i, False, True)
                else:
                    break
            st.append(t)
            sn(f'Operator {t} → push on stack', i, True)
        elif t == '(':
            st.append(t)
            sn('( → push on stack', i, True)
        elif t == ')':
            while st and st[-1] != '(':
                out.append(st.pop())
                sn('Inside brackets → pop operator to output', i, False, True)
            if st:
                st.pop()
            sn(') → discard the matching (', i)
        else:
            out.append(t)
            sn(f'Operand {t} → straight to output', i, False, True)
    while st:
        s = st.pop()
        out.append(s)
        sn(f'End of input → pop {s} to output', len(T), False, True)
    res = out[::-1] if mode == 'pre' else out
    fr.append(dict(tk=T, tok=len(T), txt=f"Result: {' '.join(res)}" + ('  (output read in reverse)' if mode == 'pre' else ''),
                   st=[], out=res, nSt=False, nOut=False))
    return fr


# ---------------------------------------------------------------- operator precedence parser
def rel(a, b):
    if a == '$':
        return 'acc' if b == '$' else 'x' if b == ')' else '<'
    if b == '$':
        return 'x' if a == '(' else '>'
    if a == 'id':
        return 'x' if b in ('id', '(') else '>'
    if a == '(':
        return '=' if b == ')' else '<'
    if a == ')':
        return 'x' if b in ('id', '(') else '>'
    if b in ('id', '('):
        return '<'
    if b == ')':
        return '>'
    x, y = PR[a], PR[b]
    return '>' if x[0] > y[0] else '<' if x[0] < y[0] else '<' if x[1] else '>'


def opp(tk):
    check_expr(tk)
    T = list(tk) + ['$']
    cl = lambda t: t if t in ('$', '(', ')') or t in PR else 'id'
    st = [dict(s='$', c='$', nt=False, tr=None)]
    fr, i = [], 0

    def top():
        for x in reversed(st):
            if not x['nt']:
                return x

    def sn(txt, a=None, b=None, r=None, hl=None, er=False):
        fr.append(dict(st=list(st), i=i, T=T, txt=txt, a=a, b=b, r=r, hl=hl, er=er,
                       roots=[x['tr'] for x in st if x['nt']]))

    sn('Start: stack holds $, input ends with $')
    for _ in range(400):
        a, b = top()['c'], cl(T[i])
        r = rel(a, b)
        if r == 'acc':
            if len(st) == 2 and st[1]['nt']:
                sn('Accept ✓ expression parsed, tree is complete', a, b, r, st[1]['tr'].id)
            else:
                sn('Error: input ended but stack is not a single expression', a, b, 'x', None, True)
            break
        if r == 'x':
            sn(f'Error: no precedence relation between {a} and {b}', a, b, r, None, True)
            break
        if r in '<=':
            st.append(dict(s=T[i], c=b, nt=False, tr=Node(T[i], True)))
            i += 1
            sn(f"{a} {'⋖' if r == '<' else '≐'} {b} → shift {T[i - 1]}", a, b, r)
        else:
            h = []
            if st[-1]['nt']:
                h.insert(0, st.pop())
            while True:
                t = st.pop()
                h.insert(0, t)
                last = t['c']
                if st and st[-1]['nt']:
                    h.insert(0, st.pop())
                if not (len(st) > 1 and rel(top()['c'], last) != '<'):
                    break
            pt = ' '.join('E' if x['nt'] else x['c'] for x in h)
            if not (pt == 'id' or (re.fullmatch(r'E \S+ E', pt) and h[1]['c'] in PR) or pt == '( E )'):
                sn(f'Error: invalid handle {pt}', a, b, 'x', None, True)
                break
            nd = Node('E', False, [x['tr'] for x in h])
            st.append(dict(s='E', c='E', nt=True, tr=nd))
            sn(f"{a} ⋗ {b} → reduce handle [{' '.join(x['s'] for x in h)}] to E", a, b, r, nd.id)
    return fr
