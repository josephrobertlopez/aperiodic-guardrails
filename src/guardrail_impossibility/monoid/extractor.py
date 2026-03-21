#!/usr/bin/env python3
"""
monoid_extractor.py
--------------------
Given a regex pattern, construct a minimal DFA, compute its syntactic
(transition) monoid M(L), check aperiodicity, and report which MOD_p
counting properties the language can distinguish.

Usage:
    python monoid_extractor.py "regex_pattern"

Requires: Python 3.8+
Optional: greenery (pip install greenery) for regex -> NFA; falls back
          to a built-in Thompson NFA constructor for common patterns.
"""

from __future__ import annotations

import sys
from collections import defaultdict, deque
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# 1.  NFA via Thompson's construction
#     Uses a module-level counter so every new_state() call yields a globally
#     unique integer — no state-ID collisions between NFA fragments.
# ---------------------------------------------------------------------------

_STATE_COUNTER = 0

def _fresh() -> int:
    global _STATE_COUNTER
    s = _STATE_COUNTER
    _STATE_COUNTER += 1
    return s


class NFA:
    """ε-NFA with globally unique integer states."""

    def __init__(self):
        # transitions[src][sym] = set of destination states
        self.transitions: Dict[int, Dict[Optional[str], Set[int]]] = \
            defaultdict(lambda: defaultdict(set))
        self.start: int = 0
        self.accept: Set[int] = set()

    def add(self, src: int, sym: Optional[str], dst: int):
        self.transitions[src][sym].add(dst)

    # ------------------------------------------------------------------
    # Thompson fragments — all return a fresh NFA with unique state IDs
    # ------------------------------------------------------------------

    @staticmethod
    def from_symbol(c: str) -> "NFA":
        n = NFA()
        s, a = _fresh(), _fresh()
        n.add(s, c, a)
        n.start, n.accept = s, {a}
        return n

    @staticmethod
    def from_empty() -> "NFA":
        """Accepts only the empty string."""
        n = NFA()
        s = _fresh()
        n.start, n.accept = s, {s}
        return n

    @staticmethod
    def from_chars(chars: List[str]) -> "NFA":
        """Union of single-character NFAs."""
        if not chars:
            return NFA.from_empty()
        parts = [NFA.from_symbol(c) for c in chars]
        result = parts[0]
        for p in parts[1:]:
            result = NFA.union(result, p)
        return result

    @staticmethod
    def concatenate(a: "NFA", b: "NFA") -> "NFA":
        n = NFA()
        _merge_into(n, a)
        _merge_into(n, b)
        for acc in a.accept:
            n.add(acc, None, b.start)
        n.start = a.start
        n.accept = set(b.accept)
        return n

    @staticmethod
    def union(a: "NFA", b: "NFA") -> "NFA":
        n = NFA()
        _merge_into(n, a)
        _merge_into(n, b)
        new_start = _fresh()
        new_accept = _fresh()
        n.add(new_start, None, a.start)
        n.add(new_start, None, b.start)
        for acc in a.accept:
            n.add(acc, None, new_accept)
        for acc in b.accept:
            n.add(acc, None, new_accept)
        n.start = new_start
        n.accept = {new_accept}
        return n

    @staticmethod
    def kleene_star(a: "NFA") -> "NFA":
        n = NFA()
        _merge_into(n, a)
        new_start = _fresh()
        new_accept = _fresh()
        n.add(new_start, None, a.start)
        n.add(new_start, None, new_accept)
        for acc in a.accept:
            n.add(acc, None, a.start)
            n.add(acc, None, new_accept)
        n.start = new_start
        n.accept = {new_accept}
        return n

    @staticmethod
    def plus(a: "NFA") -> "NFA":
        """a+ = a · a*"""
        return NFA.concatenate(a, NFA.kleene_star(_copy_nfa(a)))

    @staticmethod
    def optional(a: "NFA") -> "NFA":
        """a? = a | ε"""
        return NFA.union(a, NFA.from_empty())


def _merge_into(target: NFA, source: NFA):
    """Copy all transitions from source into target (states are globally unique)."""
    for src, mapping in source.transitions.items():
        for sym, dsts in mapping.items():
            for dst in dsts:
                target.add(src, sym, dst)


def _copy_nfa(nfa: NFA) -> "NFA":
    """Deep-copy an NFA, renaming all states to fresh IDs."""
    remap: Dict[int, int] = {}

    def remap_state(s: int) -> int:
        if s not in remap:
            remap[s] = _fresh()
        return remap[s]

    # Collect all states mentioned
    all_states: Set[int] = {nfa.start} | nfa.accept
    for src, mapping in nfa.transitions.items():
        all_states.add(src)
        for dsts in mapping.values():
            all_states.update(dsts)

    for s in all_states:
        remap_state(s)

    n = NFA()
    n.start = remap[nfa.start]
    n.accept = {remap[a] for a in nfa.accept}
    for src, mapping in nfa.transitions.items():
        for sym, dsts in mapping.items():
            for dst in dsts:
                n.add(remap[src], sym, remap[dst])
    return n


# ---------------------------------------------------------------------------
# 2.  Regex parser → NFA  (handles: literals, . [] | * + ? () {n,m} \d \w \s)
# ---------------------------------------------------------------------------

PRINTABLE = [chr(i) for i in range(32, 127)]

class RegexParser:
    """Recursive-descent parser producing Thompson NFAs."""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0

    def peek(self) -> Optional[str]:
        return self.pattern[self.pos] if self.pos < len(self.pattern) else None

    def consume(self, expected: Optional[str] = None) -> str:
        c = self.pattern[self.pos]
        if expected and c != expected:
            raise ValueError(f"Expected {expected!r} at pos {self.pos}, got {c!r}")
        self.pos += 1
        return c

    def parse(self) -> NFA:
        nfa = self.parse_alternation()
        if self.pos < len(self.pattern):
            raise ValueError(
                f"Unexpected character at pos {self.pos}: {self.pattern[self.pos]!r}"
            )
        return nfa

    def parse_alternation(self) -> NFA:
        left = self.parse_concatenation()
        while self.peek() == '|':
            self.consume('|')
            right = self.parse_concatenation()
            left = NFA.union(left, right)
        return left

    def parse_concatenation(self) -> NFA:
        result: Optional[NFA] = None
        while self.peek() not in (None, '|', ')'):
            piece = self.parse_quantifier()
            result = piece if result is None else NFA.concatenate(result, piece)
        return result if result is not None else NFA.from_empty()

    def parse_quantifier(self) -> NFA:
        base = self.parse_atom()
        q = self.peek()
        if q == '*':
            self.consume('*')
            return NFA.kleene_star(base)
        if q == '+':
            self.consume('+')
            return NFA.plus(base)
        if q == '?':
            self.consume('?')
            return NFA.optional(base)
        if q == '{':
            return self._parse_counted(base)
        return base

    def _parse_counted(self, base: NFA) -> NFA:
        self.consume('{')
        low_s = ""
        while self.peek() and self.peek().isdigit():
            low_s += self.consume()
        low = int(low_s) if low_s else 0
        high: Optional[int] = low
        if self.peek() == ',':
            self.consume(',')
            high_s = ""
            while self.peek() and self.peek().isdigit():
                high_s += self.consume()
            high = int(high_s) if high_s else None
        self.consume('}')

        parts: List[NFA] = [_copy_nfa(base) for _ in range(low)]
        if high is None:
            parts.append(NFA.kleene_star(_copy_nfa(base)))
        else:
            for _ in range(high - low):
                parts.append(NFA.optional(_copy_nfa(base)))

        if not parts:
            return NFA.from_empty()
        result = parts[0]
        for p in parts[1:]:
            result = NFA.concatenate(result, p)
        return result

    def parse_atom(self) -> NFA:
        c = self.peek()
        if c is None:
            raise ValueError("Unexpected end of pattern")
        if c == '(':
            return self._parse_group()
        if c == '[':
            return self._parse_char_class()
        if c == '.':
            self.consume('.')
            return NFA.from_chars(PRINTABLE)
        if c == '\\':
            self.consume('\\')
            return self._parse_escape()
        if c in ('*', '+', '?', '|', ')', '}'):
            raise ValueError(f"Unexpected meta-char {c!r} at pos {self.pos}")
        self.consume()
        return NFA.from_symbol(c)

    def _parse_escape(self) -> NFA:
        c = self.consume()
        mapping = {
            'd': list('0123456789'),
            'w': list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'),
            's': list(' \t\n\r\f\v'),
            'D': [ch for ch in PRINTABLE if ch not in '0123456789'],
            'W': [ch for ch in PRINTABLE
                  if ch not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'],
            'S': [ch for ch in PRINTABLE if ch not in ' \t\n\r\f\v'],
        }
        chars = mapping.get(c, [c])
        return NFA.from_chars(chars)

    def _parse_group(self) -> NFA:
        self.consume('(')
        if (self.peek() == '?' and
                self.pos + 1 < len(self.pattern) and
                self.pattern[self.pos + 1] == ':'):
            self.consume('?')
            self.consume(':')
        nfa = self.parse_alternation()
        self.consume(')')
        return nfa

    def _parse_char_class(self) -> NFA:
        self.consume('[')
        negate = False
        if self.peek() == '^':
            negate = True
            self.consume('^')
        chars: Set[str] = set()
        while self.peek() != ']':
            if self.peek() is None:
                raise ValueError("Unclosed character class")
            c = self.consume()
            if c == '\\':
                esc = self.consume()
                mapping = {
                    'd': '0123456789',
                    'w': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_',
                    's': ' \t\n\r\f\v',
                }
                chars.update(mapping.get(esc, esc))
            elif (self.peek() == '-' and
                  self.pos + 1 < len(self.pattern) and
                  self.pattern[self.pos + 1] != ']'):
                self.consume('-')
                end = self.consume()
                for code in range(ord(c), ord(end) + 1):
                    if 32 <= code < 127:
                        chars.add(chr(code))
            else:
                chars.add(c)
        self.consume(']')
        if negate:
            chars = set(PRINTABLE) - chars
        return NFA.from_chars(sorted(chars)) if chars else NFA.from_empty()


# ---------------------------------------------------------------------------
# 3.  NFA → DFA  (subset / powerset construction)
# ---------------------------------------------------------------------------

def epsilon_closure(
    transitions: Dict[int, Dict[Optional[str], Set[int]]],
    states: FrozenSet[int]
) -> FrozenSet[int]:
    stack = list(states)
    closure = set(states)
    while stack:
        s = stack.pop()
        for t in transitions[s].get(None, set()):
            if t not in closure:
                closure.add(t)
                stack.append(t)
    return frozenset(closure)


def move(
    transitions: Dict[int, Dict[Optional[str], Set[int]]],
    states: FrozenSet[int],
    symbol: str
) -> FrozenSet[int]:
    result: Set[int] = set()
    for s in states:
        result.update(transitions[s].get(symbol, set()))
    return frozenset(result)


def nfa_to_dfa(
    nfa: NFA,
    alphabet: List[str]
) -> Tuple[Dict[Tuple[int, str], int], int, Set[int], int]:
    """
    Returns (transitions, start, accept_set, num_states).
    The dead-state (empty subset) is included if needed.
    """
    trans = nfa.transitions
    start_closure = epsilon_closure(trans, frozenset({nfa.start}))
    state_map: Dict[FrozenSet[int], int] = {start_closure: 0}
    unmarked: deque[FrozenSet[int]] = deque([start_closure])
    dfa_states: List[FrozenSet[int]] = [start_closure]
    dfa_trans: Dict[Tuple[int, str], int] = {}

    DEAD = frozenset()

    while unmarked:
        current = unmarked.popleft()
        cid = state_map[current]
        for sym in alphabet:
            reachable = epsilon_closure(trans, move(trans, current, sym))
            if not reachable:
                reachable = DEAD
            if reachable not in state_map:
                state_map[reachable] = len(dfa_states)
                dfa_states.append(reachable)
                unmarked.append(reachable)
            dfa_trans[(cid, sym)] = state_map[reachable]

    accept_ids: Set[int] = {
        state_map[s] for s in dfa_states if s & nfa.accept
    }
    return dfa_trans, 0, accept_ids, len(dfa_states)


# ---------------------------------------------------------------------------
# 4.  DFA minimization (Hopcroft's algorithm)
# ---------------------------------------------------------------------------

def minimize_dfa(
    num_states: int,
    transitions: Dict[Tuple[int, str], int],
    start: int,
    accept: Set[int],
    alphabet: List[str]
) -> Tuple[int, Dict[Tuple[int, str], int], int, Set[int]]:

    # Reachability pass
    reachable: Set[int] = set()
    q: deque[int] = deque([start])
    reachable.add(start)
    while q:
        s = q.popleft()
        for sym in alphabet:
            t = transitions.get((s, sym))
            if t is not None and t not in reachable:
                reachable.add(t)
                q.append(t)

    accept_r = reachable & accept
    non_accept_r = reachable - accept_r

    if not accept_r:
        return 1, {(0, sym): 0 for sym in alphabet}, 0, set()
    if not non_accept_r:
        return 1, {(0, sym): 0 for sym in alphabet}, 0, {0}

    P: List[FrozenSet[int]] = [frozenset(accept_r), frozenset(non_accept_r)]
    W: List[FrozenSet[int]] = list(P)

    while W:
        A = W.pop()
        for sym in alphabet:
            X = frozenset(
                s for s in reachable
                if transitions.get((s, sym)) in A
            )
            if not X:
                continue
            new_P: List[FrozenSet[int]] = []
            for Y in P:
                inter = Y & X
                diff = Y - X
                if inter and diff:
                    new_P.extend([inter, diff])
                    if Y in W:
                        W.remove(Y)
                        W.extend([inter, diff])
                    else:
                        W.append(inter if len(inter) <= len(diff) else diff)
                else:
                    new_P.append(Y)
            P = new_P

    part_of: Dict[int, int] = {}
    for i, part in enumerate(P):
        for s in part:
            part_of[s] = i

    new_start = part_of[start]
    new_accept = {part_of[s] for s in accept_r}
    new_trans: Dict[Tuple[int, str], int] = {}
    for i, part in enumerate(P):
        rep = next(iter(part))
        for sym in alphabet:
            t = transitions.get((rep, sym))
            if t is not None:
                new_trans[(i, sym)] = part_of[t]

    return len(P), new_trans, new_start, new_accept


# ---------------------------------------------------------------------------
# 5.  Syntactic / transition monoid
# ---------------------------------------------------------------------------

def compute_transition_monoid(
    num_states: int,
    transitions: Dict[Tuple[int, str], int],
    start: int,
    alphabet: List[str]
) -> Tuple[List[Tuple[int, ...]], Dict[Tuple[int, int], int]]:
    """
    Returns:
        elements   — list of transformations (tuples), index = monoid element id
        mult_table — (i,j)->k meaning elements[i] then elements[j]
    """
    identity = tuple(range(num_states))

    gen_trans: Dict[str, Tuple[int, ...]] = {}
    for sym in alphabet:
        t = tuple(transitions.get((q, sym), q) for q in range(num_states))
        gen_trans[sym] = t

    elem_to_id: Dict[Tuple[int, ...], int] = {identity: 0}
    elements: List[Tuple[int, ...]] = [identity]
    queue: deque[Tuple[int, ...]] = deque([identity])

    while queue:
        current = queue.popleft()
        for sym in alphabet:
            g = gen_trans[sym]
            # compose: apply current first, then g
            composed = tuple(g[current[q]] for q in range(num_states))
            if composed not in elem_to_id:
                elem_to_id[composed] = len(elements)
                elements.append(composed)
                queue.append(composed)

    mult_table: Dict[Tuple[int, int], int] = {}
    for i, a in enumerate(elements):
        for j, b in enumerate(elements):
            composed = tuple(b[a[q]] for q in range(num_states))
            mult_table[(i, j)] = elem_to_id[composed]

    return elements, mult_table


# ---------------------------------------------------------------------------
# 6.  Aperiodicity check and group extraction
# ---------------------------------------------------------------------------

def check_aperiodic(
    elements: List[Tuple[int, ...]],
    mult_table: Dict[Tuple[int, int], int]
) -> Tuple[bool, List[int]]:
    """
    For each element m, compute powers until a cycle appears.
    If any cycle length > 1, M is not aperiodic.
    Returns (is_aperiodic, list_of_cycle_lengths > 1).
    """
    cycle_orders: List[int] = []
    for i in range(len(elements)):
        seen: Dict[int, int] = {}
        current = i
        step = 0
        while current not in seen:
            seen[current] = step
            current = mult_table[(current, i)]
            step += 1
        cycle_len = step - seen[current]
        if cycle_len > 1:
            cycle_orders.append(cycle_len)
    return (not cycle_orders), cycle_orders


def find_idempotents(
    elements: List[Tuple[int, ...]],
    mult_table: Dict[Tuple[int, int], int]
) -> List[int]:
    return [i for i in range(len(elements)) if mult_table[(i, i)] == i]


def maximal_subgroup_orders(
    elements: List[Tuple[int, ...]],
    mult_table: Dict[Tuple[int, int], int],
    idempotents: List[int]
) -> List[int]:
    """
    For each idempotent e, find its maximal subgroup in eMe and return its order if > 1.
    """
    n = len(elements)
    orders: List[int] = []
    for e in idempotents:
        # eMe = { e·m·e : m ∈ M }
        eMe: Set[int] = set()
        for m in range(n):
            eme = mult_table[(mult_table[(e, m)], e)]
            eMe.add(eme)
        # Maximal subgroup at e: invertible elements of eMe with identity e
        group: Set[int] = set()
        for m in eMe:
            if mult_table[(e, m)] == m and mult_table[(m, e)] == m:
                for m2 in eMe:
                    if mult_table[(m, m2)] == e and mult_table[(m2, m)] == e:
                        group.add(m)
                        break
        if len(group) > 1:
            orders.append(len(group))
    return orders


def prime_factors(n: int) -> List[int]:
    factors: List[int] = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


# ---------------------------------------------------------------------------
# 7.  Greenery fast-path (if installed)
# ---------------------------------------------------------------------------

def try_greenery(pattern: str):
    try:
        import greenery
        # greenery >= 4.x API
        fsm = greenery.parse(pattern).to_fsm()

        # Collect concrete alphabet (exclude the "anything else" sentinel)
        try:
            from greenery.fsm import anything_else
            sentinel = anything_else
        except ImportError:
            sentinel = None

        alphabet: List[str] = sorted(
            str(c) for c in fsm.alphabet
            if c != sentinel and isinstance(c, str) and len(str(c)) == 1
        )
        if not alphabet:
            return None

        states = sorted(fsm.states, key=lambda s: (s is not fsm.initial, s))
        state_idx: Dict = {s: i for i, s in enumerate(states)}

        num_states = len(states)
        transitions: Dict[Tuple[int, str], int] = {}
        for src, mapping in fsm.map.items():
            for sym, dst in mapping.items():
                sym_s = str(sym)
                if sym_s in alphabet and src in state_idx and dst in state_idx:
                    transitions[(state_idx[src], sym_s)] = state_idx[dst]

        start = state_idx[fsm.initial]
        accept = {state_idx[s] for s in fsm.finals if s in state_idx}
        return num_states, transitions, start, accept, alphabet
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 8.  Built-in path: regex -> NFA -> DFA -> minimize
# ---------------------------------------------------------------------------

def builtin_path(pattern: str):
    global _STATE_COUNTER
    _STATE_COUNTER = 0  # reset for reproducibility

    parser = RegexParser(pattern)
    nfa = parser.parse()

    # Collect concrete alphabet
    alphabet_set: Set[str] = set()
    for mapping in nfa.transitions.values():
        for sym in mapping:
            if sym is not None:
                alphabet_set.add(sym)
    alphabet = sorted(alphabet_set)

    if not alphabet:
        raise ValueError("Pattern contains no concrete character transitions.")

    dfa_trans, dfa_start, dfa_accept, num_dfa = nfa_to_dfa(nfa, alphabet)
    num_min, min_trans, min_start, min_accept = minimize_dfa(
        num_dfa, dfa_trans, dfa_start, dfa_accept, alphabet
    )
    return num_min, min_trans, min_start, min_accept, alphabet


# ---------------------------------------------------------------------------
# 9.  Analysis driver
# ---------------------------------------------------------------------------

def analyze(pattern: str):
    print(f"\n{'='*60}")
    print(f"  Pattern : {pattern!r}")
    print(f"{'='*60}\n")

    # --- Build minimal DFA --------------------------------------------------
    result = try_greenery(pattern)
    if result:
        num_states, transitions, start, accept, alphabet = result
        print(f"[DFA]  via greenery        |  {num_states} states  |  |Σ|={len(alphabet)}")
    else:
        try:
            num_states, transitions, start, accept, alphabet = builtin_path(pattern)
            print(f"[DFA]  via built-in NFA    |  {num_states} states  |  |Σ|={len(alphabet)}")
        except Exception as e:
            print(f"[ERROR] DFA construction failed: {e}")
            return

    print(f"       start={start}  accept={sorted(accept)}")
    print(f"       Σ = {alphabet[:12]}{'...' if len(alphabet) > 12 else ''}\n")

    # Print transition table if small
    if num_states <= 10 and len(alphabet) <= 8:
        header = "       " + "  ".join(f"{sym:>4}" for sym in alphabet)
        print(header)
        for q in range(num_states):
            mark = "*" if q in accept else (" " if q != start else ">")
            if q == start and q in accept:
                mark = ">"
            row = f"  {mark}q{q}  " + "  ".join(
                f"{transitions.get((q, sym), '-'):>4}" for sym in alphabet
            )
            print("      " + row)
        print()

    # --- Transition monoid --------------------------------------------------
    elements, mult_table = compute_transition_monoid(
        num_states, transitions, start, alphabet
    )
    print(f"[M(L)] |M| = {len(elements)} elements")

    if len(elements) <= 16:
        for i, e in enumerate(elements):
            label = "id" if i == 0 else f"m{i}"
            print(f"       {label:>4} : {e}")
    else:
        print(f"       (showing first 8 of {len(elements)})")
        for i, e in enumerate(elements[:8]):
            print(f"       m{i:>3} : {e}")
    print()

    # Multiplication table if tiny
    n = len(elements)
    if n <= 8:
        print("       Cayley table (row · col):")
        header = "        " + " ".join(f"{j:>3}" for j in range(n))
        print(header)
        for i in range(n):
            row = " ".join(f"{mult_table[(i,j)]:>3}" for j in range(n))
            print(f"       {i:>3}| {row}")
        print()

    # --- Idempotents --------------------------------------------------------
    idem = find_idempotents(elements, mult_table)
    print(f"[IDEM] {len(idem)} idempotent(s): indices {idem}\n")

    # --- Aperiodicity -------------------------------------------------------
    is_aperiodic, cycle_orders = check_aperiodic(elements, mult_table)

    if is_aperiodic:
        print("=" * 60)
        print("  RESULT : APERIODIC")
        print()
        print("  Guardrail is FO[<]-definable.")
        print("  BLIND to all modular counting — no MOD_p can be detected.")
        print("=" * 60)
    else:
        subgroup_orders = maximal_subgroup_orders(elements, mult_table, idem)
        all_orders = sorted(set(cycle_orders + subgroup_orders))

        detectable_primes: Set[int] = set()
        for order in all_orders:
            for p in prime_factors(order):
                detectable_primes.add(p)

        print("=" * 60)
        print("  RESULT : NOT APERIODIC  (nontrivial groups present)")
        print()
        print(f"  Cycle/subgroup orders : {all_orders}")
        print()
        print("  Modular predicates this guardrail CAN detect:")
        for p in sorted(detectable_primes):
            print(f"    MOD_{p}  —  strings where len ≡ k (mod {p})")
        print()
        print("  Language is NOT in FO[<].")
        print("  Guardrail is sensitive to periodic/modular structure in input.")
        print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python monoid_extractor.py \"regex_pattern\"")
        print()
        print("Examples:")
        print("  python monoid_extractor.py \"a*b*\"")
        print("  python monoid_extractor.py \"(ab)+\"")
        print("  python monoid_extractor.py \"(a|b)*abb\"")
        print("  python monoid_extractor.py \"[0-9]{3}-[0-9]{4}\"")
        sys.exit(1)

    analyze(sys.argv[1])


if __name__ == "__main__":
    main()
