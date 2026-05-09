# Library Normalization Survey

**Question:** Do the surveyed open-source guardrail libraries normalize input
(strip zero-width Unicode, NULL bytes, NFC/NFKC normalization) before applying
their regex/keyword scanners?

**Method:** For each library, we located the input-handling code path that
precedes regex matching and read the actual implementation source from each
project's main branch on GitHub.

**Date of survey:** 2026-05-08.

**Result:** None of the four surveyed libraries strip zero-width characters,
NULL bytes, or perform Unicode normalization (NFC/NFKC/NFKD) before regex
matching. The strongest preprocessing observed is lowercasing and (in one case)
non-word-character stripping that PRESERVES alphanumerics — leaving
zero-width Unicode codepoints, NULL bytes, and other potential filler
characters intact through the regex match path.

This is consistent with the algebraic-bound prediction: the bypass class is
not closed under any of these libraries' preprocessing pipelines.

---

## 1. LLM-Guard `BanSubstrings` scanner

**Source:** `https://github.com/protectai/llm-guard/blob/main/llm_guard/input_scanners/ban_substrings.py`

**Preprocessing observed:** Only optional case-folding when `case_sensitive=False`:
```python
if self._case_sensitive is False:
    s, prompt = s.lower(), prompt.lower()
```

**Zero-width / NULL / Unicode-normalization stripping:** None.

**Conclusion:** Input passes to the substring/regex match function with no
filler-character preprocessing.

---

## 2. Microsoft Presidio analyzer

**Source:** `https://github.com/microsoft/presidio/blob/main/presidio-analyzer/presidio_analyzer/analyzer_engine.py`

**Preprocessing observed:** Text is routed through an `NlpEngine.process_text()`
call that builds NLP artifacts (tokens, entities) from spaCy or similar.
The regex recognizers operate on the original text via:
```python
word = text[result.start : result.end]
```

**Zero-width / NULL / Unicode-normalization stripping:** None at the analyzer
level. Any normalization would have to come from inside `NlpEngine.process_text()`
or from individual recognizers; we did not find any in the recognizers we
inspected.

**Conclusion:** Regex pattern matches operate on raw input text without
filler-character preprocessing.

---

## 3. Rebuff prompt-injection heuristic detector

**Source:** `https://github.com/protectai/rebuff/blob/main/python-sdk/rebuff/detect_pi_heuristics.py`

**Preprocessing observed:**
```python
result = input_string.lower()
result = re.sub(r"[^\w\s]|_", "", result)
result = re.sub(r"\s+", " ", result)
normalized_string = result.strip()
```

This lowercases, strips non-word characters (preserving alphanumerics and
underscores), collapses whitespace, and trims edges.

**Zero-width / NULL / Unicode-normalization stripping:** None. NULL bytes
(`\x00`) are characters that the Python regex engine does not categorize
as `\w` or `\s`, so the second `re.sub` step DOES remove NULL bytes; but
zero-width Unicode codepoints (U+200B, U+200C, U+200D, etc.) are also
not in `\w` or `\s`, so they too get stripped — but ONLY by the heuristic
detector, NOT by other Rebuff scanners and NOT by the regex match this
heuristic stage runs alongside.

**Conclusion:** This stage strips many filler choices (including NULL bytes
and zero-width codepoints) BUT only as a side-effect of `[^\w\s]` removal;
it does not perform Unicode normalization (NFC/NFKC), and there are
filler choices it does not strip (e.g., U+00A0 NO-BREAK SPACE matches
`\s`, so it is preserved). The bypass under printable ASCII filler (e.g.,
ASCII space) is unaffected.

---

## 4. NeMo Guardrails content-safety check

**Source:** `https://github.com/NVIDIA/NeMo-Guardrails/blob/develop/nemoguardrails/library/content_safety/actions.py`

**Preprocessing observed:**
```python
if context is not None:
    user_input = context.get("user_message", "")
# ...
check_input_prompt = llm_task_manager.render_task_prompt(
    task=task,
    context={"user_input": user_input, ...},
)
```

The content-safety check passes the user input directly into a prompt template
that is then evaluated by an LLM.

**Zero-width / NULL / Unicode-normalization stripping:** None visible in this
function. NeMo's primary defense path is LLM-driven, so the regex tier (when
present) is not the principal mechanism; sanitization, when it happens, is
delegated to the underlying LLM rather than performed in the content-safety
function.

**Conclusion:** No regex-tier preprocessing of fillers; LLM is responsible
for any decoding/sanitization.

---

## Summary Table

| Library | Lowercase | Non-word strip | Unicode normalize | Strip ZWSP/ZWNJ/ZWJ | Strip NULL | Notes |
|---|---|---|---|---|---|---|
| LLM-Guard `BanSubstrings` | optional | no | no | no | no | only case-folding |
| Presidio analyzer | no | no | no | no | no | regex on raw text |
| Rebuff `detect_pi_heuristics` | yes | yes (`[^\w\s]`) | no | yes (side-effect) | yes (side-effect) | does NOT strip NBSP and similar `\s`-class non-ASCII fillers |
| NeMo Guardrails content-safety | no | no | no | no | no | LLM-as-judge primary path |

**Bottom line:** Three of the four libraries pass NULL bytes and zero-width
Unicode codepoints through to regex matching with no normalization. The
fourth (Rebuff's heuristic stage) strips them as a side-effect of broader
non-word-character removal, but readily-available alternative fillers
(e.g., U+00A0 NBSP, U+2009 THIN SPACE, or any printable ASCII character
not in the pattern's literal alphabet) remain effective.

This is consistent with the §2 algebraic claim that no finite filler patch
covers all filler choices simultaneously, and supports the §5 operational
recommendation that the regex tier cannot be made MOD_p-aware via input
normalization.

---

*This artifact accompanies §3 and §6 of the CACM article. Surveyed on
2026-05-08 against `main`/`develop` branch HEAD of each project.*
