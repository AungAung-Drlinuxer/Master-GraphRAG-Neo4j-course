#!/usr/bin/env python3
"""M01 lab — Traditional NER and Relationship Extraction.

Standard library only. Deterministic. Offline.

Run: python3 modules/01_traditional_ner_relation_extraction/lab.py
"""

import re
import sys

# --- Shared deterministic fixtures ----------------------------------------

CORPUS = (
    "Sundar Pichai visited London on 12 March 2019 to open the new Google office. "
    "Satya Nadella met Tim Cook in Paris on 3 January 2020."
)

MONTHS = (
    "January|February|March|April|May|June|July|August|September|"
    "October|November|December"
)

# Capitalized word pair — a cheap proxy for a person name.
PERSON_RE = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
DATE_RE = re.compile(r"\b\d{1,2} (?:%s) \d{4}\b" % MONTHS)

BIO_TOKENS = ["Sundar", "Pichai", "visited", "London", "on",
              "12", "March", "2019", "."]
BIO_TAGS = ["B-PER", "I-PER", "O", "B-LOC", "O",
            "B-DATE", "I-DATE", "I-DATE", "O"]

# alias -> (type, canonical)
GAZETTEER = {
    "Google": ("ORG", "Google"),
    "Google LLC": ("ORG", "Google"),
    "Alphabet": ("ORG", "Alphabet"),
    "MSFT": ("ORG", "Microsoft"),
    "Microsoft": ("ORG", "Microsoft"),
}
GAZETTEER_TEXT = ("Google LLC is a subsidiary of Alphabet. "
                  "MSFT competes with Google.")

REL_RULES = [
    (re.compile(r"(%s) is the CEO of ([A-Z][A-Za-z]+)" % PERSON_RE.pattern),
     "CEO_OF"),
    (re.compile(r"(%s) founded ([A-Z][A-Za-z]+)" % PERSON_RE.pattern),
     "FOUNDED"),
]
REL_TEXT = "Sundar Pichai is the CEO of Google. Larry Page founded Google."

COREF_TEXT = ("Sundar Pichai leads Google. He became CEO in 2015. "
              "His tenure expanded the company.")
COREF_PERSONS = {"Sundar Pichai": "M", "Larry Page": "M"}

GOLD_TRIPLES = {
    ("Sundar Pichai", "CEO_OF", "Google"),
    ("Larry Page", "FOUNDED", "Google"),
    ("Satya Nadella", "CEO_OF", "Microsoft"),
}
PRED_TRIPLES = {
    ("Sundar Pichai", "CEO_OF", "Google"),
    ("Larry Page", "FOUNDED", "Google"),
    ("Sundar Pichai", "CEO_OF", "Alphabet"),
}


# --- Exercise 1 — Regex-based NER -----------------------------------------

def regex_ner(text, patterns):
    """Return {label: [surface, ...]} using ordered regex patterns."""
    found = {}
    for label, pattern in patterns:
        found[label] = pattern.findall(text)
    return found


def exercise_1() -> bool:
    print("\n--- Exercise 1: Regex-based NER ---")
    entities = regex_ner(CORPUS, [("PER", PERSON_RE), ("DATE", DATE_RE)])
    print("PER  :", entities["PER"])
    print("DATE :", entities["DATE"])
    assert entities["PER"] == ["Sundar Pichai", "Satya Nadella", "Tim Cook"]
    assert entities["DATE"] == ["12 March 2019", "3 January 2020"]
    print("regex pattern သည် fixed surface form များကို ယုံကြည်စိတ်ချစွာ ဖမ်းသည်")
    return True


# --- Exercise 2 — BIO tagging decode --------------------------------------

def decode_bio(tokens, tags):
    """Decode BIO-tagged tokens into entity spans."""
    spans = []
    current = None
    for index, (token, tag) in enumerate(zip(tokens, tags)):
        if tag.startswith("B-"):
            if current is not None:
                spans.append(current)
            current = {"type": tag[2:], "tokens": [token],
                       "start": index, "end": index + 1}
        elif tag.startswith("I-") and current is not None and tag[2:] == current["type"]:
            current["tokens"].append(token)
            current["end"] = index + 1
        else:
            if current is not None:
                spans.append(current)
            current = None
    if current is not None:
        spans.append(current)
    return [{"type": s["type"], "text": " ".join(s["tokens"]),
             "start": s["start"], "end": s["end"]} for s in spans]


def exercise_2() -> bool:
    print("\n--- Exercise 2: BIO tagging decode ---")
    spans = decode_bio(BIO_TOKENS, BIO_TAGS)
    for span in spans:
        print("  %-5s %-15s tokens[%d:%d]" % (span["type"], span["text"],
                                              span["start"], span["end"]))
    assert len(spans) == 3
    assert spans[0] == {"type": "PER", "text": "Sundar Pichai", "start": 0, "end": 2}
    assert spans[1]["type"] == "LOC" and spans[1]["text"] == "London"
    assert spans[2]["text"] == "12 March 2019" and spans[2]["end"] == 8
    print("B- / I- transition သည် entity boundary ကို အတိအကျ သတ်မှတ်သည်")
    return True


# --- Exercise 3 — Gazetteer lookup (longest match) ------------------------

def gazetteer_lookup(text, gazetteer):
    """Longest-match, boundary-aware gazetteer scan."""
    keys = sorted(gazetteer, key=len, reverse=True)
    matches = []
    index = 0
    while index < len(text):
        for key in keys:
            end = index + len(key)
            if text.startswith(key, index) \
                    and (index == 0 or not text[index - 1].isalnum()) \
                    and (end == len(text) or not text[end].isalnum()):
                entity_type, canonical = gazetteer[key]
                matches.append({"alias": key, "type": entity_type,
                                "canonical": canonical, "start": index})
                index = end
                break
        else:
            index += 1
    return matches


def exercise_3() -> bool:
    print("\n--- Exercise 3: Gazetteer lookup ---")
    matches = gazetteer_lookup(GAZETTEER_TEXT, GAZETTEER)
    for match in matches:
        print("  %-10s -> %-10s (%s)" % (match["alias"], match["canonical"],
                                         match["type"]))
    assert [m["alias"] for m in matches] == ["Google LLC", "Alphabet", "MSFT", "Google"]
    assert [m["canonical"] for m in matches] == ["Google", "Alphabet",
                                                 "Microsoft", "Google"]
    assert all(m["type"] == "ORG" for m in matches)
    print("longest match သည် 'Google LLC' ကို 'Google' မဖြစ်စေဘဲ alias အဖြစ် ထိန်းသည်")
    return True


# --- Exercise 4 — Pattern-based relationship extraction -------------------

def extract_relations(text, rules):
    """Apply ordered regex rules; return (subject, relation, object) triples."""
    triples = []
    for pattern, relation in rules:
        for match in pattern.finditer(text):
            triples.append((match.group(1), relation, match.group(2)))
    return triples


def exercise_4() -> bool:
    print("\n--- Exercise 4: Pattern-based relationship extraction ---")
    triples = extract_relations(REL_TEXT, REL_RULES)
    for triple in triples:
        print("  (%s, %s, %s)" % triple)
    assert ("Sundar Pichai", "CEO_OF", "Google") in triples
    assert ("Larry Page", "FOUNDED", "Google") in triples
    assert len(triples) == 2
    print("pattern တိုင်းတွင် trigger verb တိကျစွာ ပါဝင်ရမည် — coverage နှင့် precision ကို လဲလှယ်သည်")
    return True


# --- Exercise 5 — Coreference resolution ----------------------------------

def resolve_coreference(text, persons):
    """Replace pronouns with the last mentioned known person."""
    name_pattern = "|".join(re.escape(name) for name in persons)
    pattern = re.compile(r"\b(%s|He|She|They|His|Her|Their)\b" % name_pattern)
    state = {"last": None}

    def replace(match):
        token = match.group(1)
        if token in persons:
            state["last"] = token
            return token
        if state["last"] is None:
            return token
        if token.lower() in {"his", "her", "their"}:
            return state["last"] + "'s"
        return state["last"]

    return pattern.sub(replace, text)


def exercise_5() -> bool:
    print("\n--- Exercise 5: Coreference resolution ---")
    resolved = resolve_coreference(COREF_TEXT, COREF_PERSONS)
    print("before:", COREF_TEXT)
    print("after :", resolved)
    assert resolved.count("Sundar Pichai") == 3
    assert "He became" not in resolved
    assert "Sundar Pichai's tenure" in resolved
    print("pronoun resolution မရှိပါက 'He' နှင့် 'Sundar Pichai' သည် node ၂ ခု ဖြစ်လာသည်")
    return True


# --- Exercise 6 — Precision / Recall / F1 ---------------------------------

def prf1(gold, predicted):
    """Return (precision, recall, f1, tp, fp, fn)."""
    true_positive = len(gold & predicted)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)
    precision = true_positive / (true_positive + false_positive) \
        if (true_positive + false_positive) else 0.0
    recall = true_positive / (true_positive + false_negative) \
        if (true_positive + false_negative) else 0.0
    f1 = 2 * precision * recall / (precision + recall) \
        if (precision + recall) else 0.0
    return precision, recall, f1, true_positive, false_positive, false_negative


def exercise_6() -> bool:
    print("\n--- Exercise 6: Precision / Recall / F1 ---")
    precision, recall, f1, tp, fp, fn = prf1(GOLD_TRIPLES, PRED_TRIPLES)
    print("gold      :", sorted(GOLD_TRIPLES))
    print("predicted :", sorted(PRED_TRIPLES))
    print("tp=%d fp=%d fn=%d" % (tp, fp, fn))
    print("precision=%.4f recall=%.4f f1=%.4f" % (precision, recall, f1))
    assert (tp, fp, fn) == (2, 1, 1)
    assert abs(precision - 0.6667) < 1e-3
    assert abs(recall - 0.6667) < 1e-3
    assert abs(f1 - 0.6667) < 1e-3
    print("triple-level exact match သည် relation type အမှားကို precision ဖြင့် ဖမ်းသည်")
    return True


# --- Runner ---------------------------------------------------------------

def run_all() -> bool:
    exercises = [
        ("1", exercise_1),
        ("2", exercise_2),
        ("3", exercise_3),
        ("4", exercise_4),
        ("5", exercise_5),
        ("6", exercise_6),
    ]
    passed = 0
    for label, function in exercises:
        if function():
            passed += 1
    if passed == len(exercises):
        print("\n[PASS] All 6/6 exercises passed successfully.")
        return True
    print("\n[FAIL] %d/6 exercises passed." % passed)
    return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
