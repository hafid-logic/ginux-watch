"""Optional Spec-Ref injection for PR bodies (phase 5, no new deps)."""
FOOTER = "Prepared with AI assistance; reviewed by me."
def with_spec_ref(body, entry):
    ref = entry.get("spec_ref")
    if not ref:
        return body
    nl = chr(10)
    line = "Spec-Ref: " + ref
    if FOOTER in body:
        return body.replace(FOOTER, line + nl + nl + FOOTER)
    return body + nl + line + nl
