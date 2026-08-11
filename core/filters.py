import re
from collections import Counter

MIN_OUT, MAX_OUT, MAX_REP = 20, 1500, 0.35

def ok_length(s):
    n = len(s.get("output",""))
    return MIN_OUT <= n <= MAX_OUT

def ok_repetition(s):
    w = s.get("output","").split()
    if len(w) < 12: return True
    grams = [" ".join(w[i:i+4]) for i in range(len(w)-3)]
    return 1 - len(set(grams))/len(grams) <= MAX_REP

def ok_grounding(s):
    c = set(re.findall(r"\b[a-z]{4,}\b", s.get("context","").lower()))
    o = [w for w in re.findall(r"\b[a-z]{4,}\b", s.get("output","").lower())]
    if not o: return False
    return sum(1 for w in o if w in c) / len(o) >= 0.15

def ok_format(s):
    return isinstance(s.get("instruction"), str) and isinstance(s.get("output"), str) and s["instruction"].strip() and s["output"].strip()

def ok_diff(s):
    diff, out = s.get("difficulty",""), s.get("output","")
    wc = len(out.split())
    if diff == "easy" and wc > 350: return False
    if diff == "hard" and wc < 30: return False
    return True

def validate(sample, apply=True):
    if not apply: return True, []
    checks = [("format", ok_format), ("length", ok_length), ("repetition", ok_repetition), ("grounding", ok_grounding), ("difficulty", ok_diff)]
    fails = [n for n, fn in checks if not fn(sample)]
    return len(fails) == 0, fails
