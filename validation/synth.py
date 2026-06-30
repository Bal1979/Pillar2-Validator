"""
Defekt-synthesizer: byg et minimalt XML-input der planter ÉN defekt målrettet
en given OECD-regel ud fra dens `check`-definition. Bruges af run_validation.

Princippet: for hver check-type konstrueres den mindst mulige overtrædelse, så
netop denne regel fyrer i motoren (validator.rules.oecd_rules.evaluate). Paths i
kataloget bruger et begrænset sæt former, som path-byggeren herunder forstår:
`globe:Navn`, `stf:Navn`, `*[local-name()='Navn']`, exists-prædikater
`*[globe:Barn]`, lighed `globe:Navn[.='v']` / `Navn[globe:Barn='v']`,
afsluttende `@Attribut`, og union `A | B` (første alternativ bygges).
"""

from __future__ import annotations

import re
from typing import Optional

from lxml import etree

NS = {
    "globe": "urn:oecd:ties:globe:v2",
    "stf": "urn:oecd:ties:globestf:v5",
    "iso": "urn:oecd:ties:isoglobetypes:v1",
}


class Unsynthesizable(Exception):
    """Rejses når en check ikke kan synthetiseres automatisk."""


def _qname(prefix_name: str) -> str:
    if ":" in prefix_name:
        pfx, local = prefix_name.split(":", 1)
    else:
        pfx, local = "globe", prefix_name
    if pfx not in NS:
        raise Unsynthesizable(f"ukendt prefiks: {prefix_name}")
    return "{%s}%s" % (NS[pfx], local)


_LOCAL_NAME = re.compile(r"^\*\[local-name\(\)=['\"]([^'\"]+)['\"]\]$")
_PRED_SELF = re.compile(r"\[\.=['\"]([^'\"]+)['\"]\]")
_PRED_CHILD_EQ = re.compile(r"\[((?:\w+:)?[\w.\-]+)=['\"]([^'\"]+)['\"]\]")
_PRED_CHILD_EXISTS = re.compile(r"\[((?:\w+:)?[\w.\-]+)\]")


def _attr_qname(name: str) -> str:
    return _qname(name) if ":" in name else name


def _split_steps(path: str):
    steps, depth, cur = [], 0, ""
    for ch in path:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "/" and depth == 0:
            steps.append(cur); cur = ""
        else:
            cur += ch
    if cur:
        steps.append(cur)
    return steps


def _make_step(parent, step: str, reuse: bool):
    """Skab (eller genbrug) ét trin. Returnér elementet."""
    lm = _LOCAL_NAME.match(step)
    if lm:
        return etree.SubElement(parent, _qname("globe:" + lm.group(1)))

    bi = step.find("[")
    base = step if bi == -1 else step[:bi]
    pred = "" if bi == -1 else step[bi:]

    if base in ("*", ""):
        el = etree.SubElement(parent, _qname("globe:Ctx"))
    elif pred == "" and reuse:
        qn = _qname(base)
        ex = parent.find(qn)
        el = ex if ex is not None else etree.SubElement(parent, qn)
    else:
        el = etree.SubElement(parent, _qname(base))

    if pred:
        m = _PRED_SELF.search(pred)
        if m:
            el.text = m.group(1)
        elif _PRED_CHILD_EQ.search(pred):
            m = _PRED_CHILD_EQ.search(pred)
            etree.SubElement(el, _qname(m.group(1))).text = m.group(2)
        elif _PRED_CHILD_EXISTS.search(pred):
            m = _PRED_CHILD_EXISTS.search(pred)
            etree.SubElement(el, _qname(m.group(1)))
        else:
            raise Unsynthesizable(f"ukendt prædikat: {step}")
    return el


def ensure_path(parent, path: str, text: Optional[str] = None,
                set_attr: Optional[str] = None, reuse: bool = True):
    """Skab sti `path` under `parent` (find-or-create) og returnér leaf."""
    path = path.strip()
    if "|" in path:                       # union → byg første alternativ
        path = path.split("|")[0].strip()
    for pfx in (".//", "//", "./"):
        if path.startswith(pfx):
            path = path[len(pfx):]
    node = parent
    if path not in (".", ""):
        for step in _split_steps(path):
            if step.startswith("@"):
                node.set(_attr_qname(step[1:]), text if text is not None else "X")
                return node
            node = _make_step(node, step, reuse)
    if set_attr:
        node.set(_attr_qname(set_attr), text if text is not None else "X")
    elif text is not None:
        node.text = text
    return node


# ---------------------------------------------------------------------------
# Rod + periode
# ---------------------------------------------------------------------------
def _root():
    return etree.Element(_qname("globe:GLOBE_OECD"), nsmap=NS)


def _with_period(root, start="2024-01-01", end="2024-12-31"):
    p = etree.SubElement(root, _qname("globe:Period"))
    etree.SubElement(p, _qname("globe:Start")).text = start
    etree.SubElement(p, _qname("globe:End")).text = end


# ---------------------------------------------------------------------------
# Betingelses-helpers (numerisk coercion på lt/le/gt/ge)
# ---------------------------------------------------------------------------
def _numstr(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else str(x)


from datetime import date as _date


def _put(root, cont, path, text):
    """Skab path med tekst — absolut (// eller /) under root, ellers under cont."""
    if path.startswith("/"):
        ensure_path(root, path, text=text)
    else:
        ensure_path(cont, path, text=text)


def _anchor(as_t):
    """Basisværdi for en ref-grænse: (numerisk, streng-til-element)."""
    if as_t == "year":
        return 2024, "2024"
    if as_t == "date":
        return _date(2024, 6, 30), "2024-06-30"
    return 100.0, "100"


def _pick(op, as_t, T, satisfy):
    """Returnér en streng-værdi der opfylder (satisfy) eller bryder op vs. grænsen T."""
    if as_t == "date":
        Y = T.year
        true_v = {"gt": _date(Y + 1, 1, 1), "ge": _date(Y, T.month, T.day),
                  "lt": _date(Y - 1, 12, 31), "le": _date(Y, T.month, T.day),
                  "eq": _date(Y, T.month, T.day), "ne": _date(Y + 1, 1, 1)}
        false_v = {"gt": _date(Y - 1, 1, 1), "ge": _date(Y - 1, 1, 1),
                   "lt": _date(Y + 1, 1, 1), "le": _date(Y + 1, 1, 1),
                   "eq": _date(Y + 1, 1, 1), "ne": _date(Y, T.month, T.day)}
        return (true_v if satisfy else false_v)[op].isoformat()
    T = float(T)
    pair = {"gt": (T + 1, T - 1), "ge": (T, T - 1), "lt": (T - 1, T + 1),
            "le": (T, T + 1), "eq": (T, T + 1), "ne": (T + 1, T)}[op]
    v = pair[0] if satisfy else pair[1]
    return str(int(v)) if (as_t == "year" or float(v).is_integer()) else str(v)


def _numeric_cond(root, cont, cond, satisfy):
    """Plant en numerisk/dato/år-betingelse (med evt. ref/offset/as)."""
    op, as_t = cond["op"], cond.get("as")
    offset = cond.get("offset", 0)
    if "ref" in cond:
        Tnum, refstr = _anchor(as_t)
        _put(root, cont, cond["ref"], refstr)
        T = Tnum + offset if as_t != "date" else Tnum
    else:
        T = _cnum_synth(cond.get("value"), as_t)
        if T is not None and as_t != "date":
            T = T + offset
    ensure_path(cont, cond["path"], text=_pick(op, as_t, T, satisfy), reuse=False)


def _cnum_synth(v, as_t):
    if as_t == "date":
        return _date.fromisoformat(str(v)[:10])
    if as_t == "year":
        import re as _re
        m = _re.search(r"\d{4}", str(v))
        return int(m.group(0)) if m else None
    return float(v)


def _cond_satisfy(root, cont, cond):
    path, op, val = cond["path"], cond["op"], cond.get("value")
    if op == "present":
        ensure_path(cont, path)
    elif op == "equals":
        ensure_path(cont, path, text=str(val))
    elif op == "in":
        ensure_path(cont, path, text=str(val[0] if isinstance(val, list) else val))
    elif op == "contains":
        ensure_path(cont, path, text=str(val))
    elif op in ("not_equals", "not_in"):
        ensure_path(cont, path, text="ZZZ-unmatched")
    elif op == "absent":
        pass
    elif op in ("lt", "le", "gt", "ge", "eq", "ne"):
        _numeric_cond(root, cont, cond, satisfy=True)


def _cond_violate(root, cont, cond):
    """Gør then-betingelsen FALSK. Vigtigt: når then deler path med en when-
    betingelse (samme element), må vi IKKE overskrive when-værdien — derfor
    tilføjer not_in/not_equals/contains et NYT sibling-element (reuse=False),
    og equals/in gør INTET (manglende/forkert værdi gør allerede then falsk)."""
    path, op, val = cond["path"], cond["op"], cond.get("value")
    if op in ("present", "equals", "in"):
        pass                                   # manglende/forkert → then falsk
    elif op == "absent":
        ensure_path(cont, path, text="X", reuse=False)
    elif op == "not_equals":
        ensure_path(cont, path, text=str(val), reuse=False)
    elif op == "not_in":
        ensure_path(cont, path, text=str(val[0] if isinstance(val, list) else val),
                    reuse=False)
    elif op == "contains":
        ensure_path(cont, path, text="ZZZ-without-token", reuse=False)
    elif op in ("lt", "le", "gt", "ge", "eq", "ne"):
        _numeric_cond(root, cont, cond, satisfy=False)


def _container(root, path):
    return root if path in (".", "") else ensure_path(root, path, reuse=False)


def _zero_formula(cont, formula):
    """Sæt alle felt-operander til 1, så computed bliver et endeligt tal (≠ target
    999999) UDEN risiko for division med nul i divide-formler."""
    if isinstance(formula, (int, float)):
        return
    if formula.get("op") == "sum_all":
        ensure_path(cont, formula["path"], text="1", reuse=False)
        return
    for operand in formula.get("operands", []):
        if isinstance(operand, dict):
            _zero_formula(cont, operand)
        elif isinstance(operand, (int, float)):
            continue
        else:
            ensure_path(cont, operand, text="1")


def _breaking_pair(op, as_t):
    """Returnér (left, right) som STRENGE der BRYDER `op` under coercion `as_t`.
    le/lt kræver venstre ≤/<; bryd med venstre > højre. ge/gt → venstre < højre.
    eq → forskellige; ne → ens."""
    need_greater = op in ("le", "lt")          # bryd: left > right
    need_less = op in ("ge", "gt")             # bryd: left < right
    if as_t == "date":
        hi, lo = "2025-06-01", "2023-01-01"
    elif as_t == "year":
        hi, lo = "2030", "2020"
    elif as_t == "number":
        hi, lo = "10", "1"
    else:
        hi, lo = "BBB", "AAA"
    mid = lo
    if op == "eq":
        return (hi, lo)                        # forskellige → bryder eq
    if op == "ne":
        return (mid, mid)                      # ens → bryder ne
    if need_greater:
        return (hi, lo)
    if need_less:
        return (lo, hi)
    return (hi, lo)


# ---------------------------------------------------------------------------
# Hoved: synth_defect
# ---------------------------------------------------------------------------
def synth_defect(rule: dict) -> Optional[bytes]:
    """Byg XML-bytes med ÉN planted defekt for `rule`, eller None hvis check-typen
    ikke kan synthetiseres automatisk."""
    chk = rule["check"]
    t = chk["type"]
    root = _root()
    try:
        if t == "unique":
            for _ in range(2):
                ensure_path(root, chk["xpath"], text="DUP-1", reuse=False)
            return _ser(root)

        if t == "unique_in":
            cont = _container(root, chk["container"])
            for _ in range(2):
                ensure_path(cont, chk["xpath"], text="DUP-1", reuse=False)
            return _ser(root)

        if t in ("required_if", "forbidden_if"):
            cont = _container(root, chk["container"])
            ensure_path(cont, chk["when"], text=chk["when_in"][0])
            if t == "forbidden_if":
                ensure_path(cont, chk["forbid"], text="X")
            return _ser(root)

        if t == "not_equal":
            cont = _container(root, chk["container"])
            ensure_path(cont, chk["left"], text="SAME")
            ensure_path(cont, chk["right"], text="SAME")
            return _ser(root)

        if t == "mutually_exclusive":
            ensure_path(root, chk["xpath"], text=chk["group_a"][0], reuse=False)
            ensure_path(root, chk["xpath"], text=chk["group_b"][0], reuse=False)
            return _ser(root)

        if t == "conditional":
            cont = _container(root, chk["container"])
            for c in chk.get("when", []):
                _cond_satisfy(root, cont, c)
            if chk["then"]:
                _cond_violate(root, cont, chk["then"][0])
            return _ser(root)

        if t == "conditional_ref":
            cont = _container(root, chk["container"])
            for c in chk.get("when", []):
                _cond_satisfy(root, cont, c)
            ensure_path(cont, chk["source"], text="ORPHAN-REF", reuse=False)
            return _ser(root)

        if t == "value_range":
            if "max" in chk:
                bad = chk["max"] + 1
            elif "min" in chk:
                bad = chk["min"] - 1
            elif chk.get("exclude") is not None:
                bad = chk["exclude"]
            else:
                return None
            ensure_path(root, chk["xpath"], text=str(bad))
            return _ser(root)

        if t == "compare":
            _with_period(root)
            cont = _container(root, chk["container"])
            left_val, right_val = _breaking_pair(chk["op"], chk.get("as"))
            ensure_path(cont, chk["left"], text=left_val)
            rp = chk["right"]
            if rp.startswith("/"):
                existing = root.xpath(rp, namespaces=NS)
                if existing:
                    existing[0].text = right_val
                else:
                    ensure_path(root, rp, text=right_val)
            else:
                ensure_path(cont, rp, text=right_val)
            return _ser(root)

        if t == "calculation":
            cont = _container(root, chk["container"])
            ensure_path(cont, chk["target"], text="999999")
            _zero_formula(cont, chk["formula"])
            return _ser(root)

        if t == "cardinality":
            cont = _container(root, chk["container"])
            if "max" in chk:
                for _ in range(chk["max"] + 1):
                    ensure_path(cont, chk["path"], text="X", reuse=False)
                return _ser(root)
            return None

        if t == "ref_integrity":
            ensure_path(root, chk["source"], text="ORPHAN-REF", reuse=False)
            return _ser(root)

        if t == "format":
            ensure_path(root, chk["xpath"], text="###INVALID-FORMAT###")
            return _ser(root)
    except Unsynthesizable:
        return None
    return None


def _ser(root) -> bytes:
    return etree.tostring(root)
