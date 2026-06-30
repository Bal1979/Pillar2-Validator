"""
OECD-regelmotor (lag 3 file-level / lag 4 record-level).

Indlæser de maskinlæsbare regler fra reference/oecd_validation_rules.json og
evaluerer dem mod en parset GIR-tree med XPath. Hver regel har en `check` med
en type — evaluatoren er data-drevet, så nye OECD-regler tilføjes i JSON'en,
ikke i koden.

Understøttede check-typer:
  - unique       : alle værdier på en XPath skal være entydige (file-level)
  - required_if  : i hver container: hvis felt ∈ mængde, skal et andet felt findes
  - forbidden_if : i hver container: hvis felt ∈ mængde, må et andet felt ikke findes
  - not_equal    : i hver container: to felter må ikke være ens
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Dict, List, Optional

_REFERENCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "reference",
)
RULES_PATH = os.path.join(_REFERENCE_DIR, "oecd_validation_rules.json")
CATALOGUE_PATH = os.path.join(_REFERENCE_DIR, "oecd_validation_rules_catalogue.json")


class OecdRulesError(Exception):
    pass


@lru_cache(maxsize=1)
def load_oecd_rules(path: str = RULES_PATH) -> Dict:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    validate_ruleset(data)
    return data


_VALID_TYPES = {"unique", "required_if", "forbidden_if", "not_equal",
                "mutually_exclusive", "conditional", "ref_integrity",
                "format", "value_range", "compare", "cardinality",
                "conditional_ref", "calculation", "unique_in"}
_VALID_LEVELS = {"file", "record"}


@lru_cache(maxsize=1)
def load_catalogue(path: str = CATALOGUE_PATH) -> Dict:
    """Den fulde officielle regelliste (163 regler) — referencegrundlag."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def switched_off_codes() -> frozenset:
    """OECD-regelnumre slået fra for første filing-cyklus (juni-2026-guidance).
    Disse fyres ALDRIG af motoren, selv hvis de implementeres."""
    try:
        cat = load_catalogue()
    except Exception:
        return frozenset()
    return frozenset(r["code"] for r in cat.get("rules", []) if r.get("switched_off_2026"))


def coverage() -> Dict:
    """Dækningsstatistik: hvor mange af de officielle regler er eksekverbare,
    samt scope-fordeling (executable / covered_by / candidate / out_of_scope /
    switched_off) fra kataloget. file_validatable = alt undtagen switched_off og
    out_of_scope; effektivt dækket = executable + covered_by."""
    try:
        rules = load_catalogue().get("rules", [])
    except Exception:
        rules = []
    total = len(rules)
    executable = len(load_oecd_rules().get("rules", []))
    scope: Dict[str, int] = {}
    for r in rules:
        scope[r.get("scope", "candidate")] = scope.get(r.get("scope", "candidate"), 0) + 1
    covered_by = scope.get("covered_by", 0)
    out_of_scope = scope.get("out_of_scope", 0)
    file_validatable = total - scope.get("switched_off", 0) - out_of_scope
    return {"total_catalogue": total, "executable": executable,
            "switched_off": len(switched_off_codes()),
            "scope": scope, "covered_by": covered_by, "out_of_scope": out_of_scope,
            "candidates": scope.get("candidate", 0),
            "file_validatable": file_validatable,
            "effectively_covered": executable + covered_by}


def validate_ruleset(data: Dict) -> None:
    """Lint: rejser OecdRulesError ved strukturelle fejl (bruges af sync-tool)."""
    if "namespaces" not in data or "rules" not in data:
        raise OecdRulesError("mangler 'namespaces' eller 'rules'.")
    for r in data["rules"]:
        for f in ("id", "level", "name_da", "check", "message_da"):
            if f not in r:
                raise OecdRulesError(f"regel mangler felt '{f}': {r.get('id', '?')}")
        if r["level"] not in _VALID_LEVELS:
            raise OecdRulesError(f"{r['id']}: ukendt level {r['level']!r}")
        t = r["check"].get("type")
        if t not in _VALID_TYPES:
            raise OecdRulesError(f"{r['id']}: ukendt check-type {t!r}")


def _txt(node, expr: str, ns: Dict) -> Optional[str]:
    res = node.xpath(expr, namespaces=ns)
    if not res:
        return None
    el = res[0]
    text = getattr(el, "text", el)
    return text.strip() if isinstance(text, str) and text.strip() else (
        el.strip() if isinstance(el, str) else None)


def _values(node, path: str, ns: Dict) -> List[str]:
    """Returnér streng-værdier for en relativ path: '.' = elementets tekst,
    '@attr' = attributværdi, ellers child-elementers tekst. [] hvis fraværende."""
    if path == ".":
        return [(node.text or "").strip()] if (node.text or "").strip() else []
    res = node.xpath(path, namespaces=ns)
    out = []
    for r in res:
        if isinstance(r, str):           # attribut
            if r.strip():
                out.append(r.strip())
        else:                            # element
            if (r.text or "").strip():
                out.append(r.text.strip())
    return out


def _cond_holds(node, cond: Dict, ns: Dict) -> bool:
    """Evaluér én betingelse {path, op, value} mod node. Operatorer:
    present/absent, equals/not_equals, in/not_in, contains."""
    op = cond["op"]
    path = cond["path"]
    if op in ("present", "absent"):
        # Eksistens, ikke tekst — et tomt element (<X/>) tæller som til stede.
        exists = (path == "." or len(node.xpath(path, namespaces=ns)) > 0)
        return exists if op == "present" else not exists
    vals = _values(node, path, ns)
    val = cond.get("value")
    if not vals:                         # de resterende kræver en værdi
        return op in ("not_equals", "not_in")   # fravær opfylder "må ikke"
    if op == "equals":
        return any(v == val for v in vals)
    if op == "not_equals":
        return all(v != val for v in vals)
    if op == "in":
        return any(v in val for v in vals)
    if op == "not_in":
        return all(v not in val for v in vals)
    if op == "contains":
        return any(val in v for v in vals)
    if op in ("lt", "gt", "le", "ge", "eq", "ne"):
        # Numerisk/dato-/år-sammenligning. 'as' styrer coercion (number/year/date),
        # 'ref' tager sammenligningsværdien fra et andet element (i stedet for en
        # litteral 'value'), og 'offset' lægges til år/tal-grænsen (fx End.year-4).
        as_t = cond.get("as")
        if "ref" in cond:
            rvals = _values(node, cond["ref"], ns)
            target = _cnum(rvals[0], as_t) if rvals else None
        else:
            target = _cnum(val, as_t)
        if target is None:
            return False
        offset = cond.get("offset", 0)
        if offset and not hasattr(target, "isoformat"):   # år/tal — ikke dato
            target = target + offset
        cmp = {"lt": lambda n: n < target, "gt": lambda n: n > target,
               "le": lambda n: n <= target, "ge": lambda n: n >= target,
               "eq": lambda n: n == target, "ne": lambda n: n != target}[op]
        out = []
        for v in vals:
            cv = _cnum(v, as_t)
            if cv is None:
                return False
            out.append(cmp(cv))
        return any(out)
    raise OecdRulesError(f"ukendt operator: {op!r}")


def _cnum(v, as_t):
    """Coerce v til tal/år/dato. Uden 'as' antages float (bagudkompatibelt)."""
    if as_t in ("date", "year", "number"):
        return _coerce(str(v), as_t)
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _num(node, path: str, ns: Dict):
    """Returnér den numeriske værdi på en relativ path, ellers None."""
    res = node.xpath(path, namespaces=ns)
    if not res:
        return None
    el = res[0]
    txt = el if isinstance(el, str) else getattr(el, "text", None)
    if txt is None or not str(txt).strip():
        return None
    try:
        return int(str(txt).strip())
    except ValueError:
        try:
            return float(str(txt).strip())
        except ValueError:
            return None


def _eval_formula(node, f: Dict, ns: Dict):
    """Evaluér en formel {op, operands}. Operander er enten relative paths
    (numeriske felter) eller indlejrede formler. None hvis et felt mangler."""
    op = f["op"]
    if op == "sum_all":
        # Summér ALLE elementer der matcher 'path'. Tom = 0.
        total = 0
        for el in node.xpath(f["path"], namespaces=ns):
            txt = el if isinstance(el, str) else getattr(el, "text", None)
            try:
                total += int(str(txt).strip())
            except (ValueError, TypeError, AttributeError):
                return None
        return total
    vals = []
    for o in f["operands"]:
        if isinstance(o, dict):
            v = _eval_formula(node, o, ns)
        elif isinstance(o, (int, float)):
            v = o                       # litteral konstant (fx 0.15)
        else:
            v = _num(node, o, ns)
        if v is None:
            return None
        vals.append(v)
    if not vals:
        return None
    if op in ("subtract", "sub"):
        return vals[0] - sum(vals[1:])
    if op in ("sum", "add"):
        return sum(vals)
    if op in ("multiply", "mul"):
        r = 1
        for v in vals:
            r *= v
        return r
    if op in ("divide", "div"):
        return vals[0] / vals[1] if len(vals) >= 2 and vals[1] else None
    raise OecdRulesError(f"ukendt formel-operator: {op!r}")


def _render(template: str, params: Dict) -> str:
    class _Missing(dict):
        def __missing__(self, k):  # type: ignore[override]
            return "{" + k + "}"
    try:
        return template.format_map(_Missing(params))
    except Exception:
        return template


def evaluate(root, ruleset: Dict) -> List[Dict]:
    """
    Kør alle regler mod `root` (lxml-element). Returnerer en liste af
    overtrædelser: {rule, level, line, xpath, detail}.
    """
    ns = ruleset["namespaces"]
    off = switched_off_codes()
    out: List[Dict] = []

    for rule in ruleset["rules"]:
        # Respektér juni-2026-guidance: regler slået fra fyres aldrig.
        if rule.get("oecd_rule") in off:
            continue
        chk = rule["check"]
        t = chk["type"]

        if t == "unique":
            seen: Dict[str, int] = {}
            for el in root.xpath(chk["xpath"], namespaces=ns):
                val = (el.text or "").strip()
                if not val:
                    continue
                seen[val] = seen.get(val, 0) + 1
                if seen[val] > 1:
                    out.append(_violation(rule, el, {"value": val}))

        elif t in ("required_if", "forbidden_if"):
            for cont in root.xpath(chk["container"], namespaces=ns):
                when_val = _txt(cont, chk["when"], ns)
                if when_val is None or when_val not in chk["when_in"]:
                    continue
                target = chk.get("require") or chk.get("forbid")
                present = bool(cont.xpath(target, namespaces=ns))
                bad = (t == "required_if" and not present) or \
                      (t == "forbidden_if" and present)
                if bad:
                    out.append(_violation(rule, cont, {"when_value": when_val}))

        elif t == "not_equal":
            for cont in root.xpath(chk["container"], namespaces=ns):
                left = _txt(cont, chk["left"], ns)
                right = _txt(cont, chk["right"], ns)
                if left is not None and right is not None and left == right:
                    out.append(_violation(rule, cont, {"value": left}))

        elif t == "mutually_exclusive":
            # Værdierne på xpath må ikke indeholde både noget fra group_a og
            # noget fra group_b (fx OECD1 må ikke optræde sammen med OECD2/3).
            vals = [(el.text or "").strip()
                    for el in root.xpath(chk["xpath"], namespaces=ns)]
            has_a = any(v in chk["group_a"] for v in vals)
            has_b = any(v in chk["group_b"] for v in vals)
            if has_a and has_b:
                node = root.xpath(chk["xpath"], namespaces=ns)
                out.append(_violation(rule, node[0] if node else root, {}))

        elif t == "conditional":
            # For hver container: hvis ALLE 'when' holder, skal ALLE 'then' holde.
            for cont in root.xpath(chk["container"], namespaces=ns):
                if not all(_cond_holds(cont, c, ns) for c in chk.get("when", [])):
                    continue
                if not all(_cond_holds(cont, a, ns) for a in chk["then"]):
                    out.append(_violation(rule, cont, {}))

        elif t == "calculation":
            # Sammenlign rapporteret målværdi med beregnet værdi fra en formel.
            tol = chk.get("tolerance", 0)
            for cont in root.xpath(chk["container"], namespaces=ns):
                reported = _num(cont, chk["target"], ns)
                computed = _eval_formula(cont, chk["formula"], ns)
                if reported is None or computed is None:
                    continue  # mangler felter → kan ikke beregnes, spring over
                if abs(computed - reported) > tol:
                    out.append(_violation(rule, cont,
                                          {"reported": reported, "computed": computed}))

        elif t == "unique_in":
            # Værdier på 'xpath' skal være entydige INDEN FOR hver container.
            for cont in root.xpath(chk["container"], namespaces=ns):
                seen: Dict[str, int] = {}
                for el in cont.xpath(chk["xpath"], namespaces=ns):
                    v = (el.text or "").strip()
                    if not v:
                        continue
                    seen[v] = seen.get(v, 0) + 1
                    if seen[v] > 1:
                        out.append(_violation(rule, el, {"value": v}))

        elif t == "cardinality":
            # Antal forekomster af 'path' i hver container skal være inden for [min,max].
            for cont in root.xpath(chk["container"], namespaces=ns):
                n = len(cont.xpath(chk["path"], namespaces=ns))
                bad = (("max" in chk and n > chk["max"]) or
                       ("min" in chk and n < chk["min"]))
                if bad:
                    out.append(_violation(rule, cont, {"count": n}))

        elif t == "ref_integrity":
            # Hver værdi på 'source' skal findes blandt værdierne på 'target'.
            targets = {(el.text or "").strip()
                       for el in root.xpath(chk["target"], namespaces=ns)
                       if (el.text or "").strip()}
            for el in root.xpath(chk["source"], namespaces=ns):
                v = (el.text or "").strip()
                if v and v not in targets:
                    out.append(_violation(rule, el, {"value": v}))

        elif t == "conditional_ref":
            # Hvis 'when' holder i en container, skal 'source'-værdier findes
            # blandt 'target'-værdierne (dokument-bredt referenceopslag).
            targets = {(el.text or "").strip()
                       for el in root.xpath(chk["target"], namespaces=ns)
                       if (el.text or "").strip()}
            for cont in root.xpath(chk["container"], namespaces=ns):
                if not all(_cond_holds(cont, c, ns) for c in chk.get("when", [])):
                    continue
                for el in cont.xpath(chk["source"], namespaces=ns):
                    v = (el.text or "").strip()
                    if v and v not in targets:
                        out.append(_violation(rule, el, {"value": v}))

        elif t == "format":
            pat = re.compile(chk["pattern"])
            for el in root.xpath(chk["xpath"], namespaces=ns):
                v = (el.text or "").strip()
                if v and not pat.fullmatch(v):
                    out.append(_violation(rule, el, {"value": v}))

        elif t == "value_range":
            for el in root.xpath(chk["xpath"], namespaces=ns):
                raw = (el.text or "").strip()
                try:
                    num = float(raw)
                except ValueError:
                    continue
                bad = (("min" in chk and num < chk["min"]) or
                       ("max" in chk and num > chk["max"]) or
                       (chk.get("exclude") is not None and num == chk["exclude"]))
                if bad:
                    out.append(_violation(rule, el, {"value": raw}))

        elif t == "compare":
            for cont in root.xpath(chk["container"], namespaces=ns):
                left = _txt(cont, chk["left"], ns)
                right = _txt(cont, chk["right"], ns)
                if left is None or right is None:
                    continue
                a, b = _coerce(left, chk.get("as")), _coerce(right, chk.get("as"))
                if a is None or b is None:
                    continue
                op = chk["op"]
                ok = {"le": a <= b, "lt": a < b, "ge": a >= b,
                      "gt": a > b, "eq": a == b, "ne": a != b}.get(op)
                if ok is False:
                    out.append(_violation(rule, cont, {"left": left, "right": right}))

    return out


def _coerce(s: str, as_type: Optional[str]):
    """Konvertér streng til dato/tal til sammenligning. None hvis ikke muligt."""
    try:
        if as_type == "date":
            from datetime import date
            return date.fromisoformat(s[:10])
        if as_type == "year":
            m = re.search(r"\d{4}", s)   # udtræk år fra dato/gYear/heltal
            return int(m.group(0)) if m else None
        if as_type == "number":
            return float(s)
    except (ValueError, TypeError):
        return None
    return s


def _violation(rule: Dict, node, params: Dict) -> Dict:
    return {
        "rule": rule,
        "level": rule["level"],
        "line": getattr(node, "sourceline", None),
        "xpath": rule["check"].get("xpath") or rule["check"].get("container"),
        "detail": _render(rule["message_da"], params),
    }
