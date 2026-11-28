"""triage v3: precise delete-arm and fn-retval synthesis."""
import re

def synth_del_arm_v3(lines, ln, col, desc, fname):
    idx = ln - 1
    if idx >= len(lines): return None
    ci = col - 1
    text = chr(10).join(lines[idx:])
    arrow = text.find('=>', ci)
    if arrow < 0: return None
    pos = arrow + 2
    depth_b = 0; depth_p = 0; depth_k = 0
    in_str = False; in_chr = False; esc = False
    end_pos = None
    BS = chr(92)
    while pos < len(text):
        c = text[pos]
        if esc: esc = False; pos += 1; continue
        if c == BS and (in_str or in_chr): esc = True; pos += 1; continue
        if c == '"' and not in_chr: in_str = not in_str; pos += 1; continue
        if c == "'" and not in_str: in_chr = not in_chr; pos += 1; continue
        if in_str or in_chr: pos += 1; continue
        if c == '{': depth_b += 1
        elif c == '}':
            if depth_b == 0: end_pos = pos; break
            depth_b -= 1
            if depth_b == 0:
                np = pos + 1
                while np < len(text) and text[np] in ' \t\n': np += 1
                if np < len(text) and text[np] == ',': np += 1
                end_pos = np; break
        elif c == '(': depth_p += 1
        elif c == ')': depth_p -= 1
        elif c == '[': depth_k += 1
        elif c == ']': depth_k -= 1
        elif c == ',' and depth_b == 0 and depth_p == 0 and depth_k == 0:
            end_pos = pos + 1; break
        pos += 1
    if end_pos is None: return None
    arm_text = text[ci:end_pos]
    whole = chr(10).join(lines)
    if whole.count(arm_text) == 1:
        return {"name": f"del-arm-v3-{ln}", "old": arm_text, "new": "", "line": ln}
    if idx > 0:
        ctx = lines[idx - 1] + chr(10) + arm_text
        if whole.count(ctx) == 1:
            return {"name": f"del-arm-v3-{ln}", "old": ctx, "new": lines[idx - 1], "line": ln}
    return None

def synth_fn_ret_v3(lines, ln, col, desc, fname):
    m = re.match(r"^replace (.+?) -> ([^ ]+) with (.+?) in ", desc)
    if not m: return None
    y = m.group(3)
    i = min(ln, len(lines)) - 1
    sig_idx = None
    while i >= 0:
        fm = re.search(r'\bfn\s+([a-zA-Z0-9_]+)', lines[i])
        if fm and '//' not in lines[i].split('fn')[0]:
            sig_idx = i; break
        i -= 1
    if sig_idx is None: return None
    brace_idx = None
    for k in range(sig_idx, min(len(lines), sig_idx + 5)):
        if '{' in lines[k]: brace_idx = k; break
    if brace_idx is None: return None
    depth = 0; opened = False; end_idx = None
    for j in range(brace_idx, len(lines)):
        for ch in lines[j]:
            if ch == '{': depth += 1; opened = True
            elif ch == '}':
                depth -= 1
                if opened and depth == 0: end_idx = j; break
        if end_idx is not None: break
    if end_idx is None: return None
    old_full = chr(10).join(lines[sig_idx:end_idx + 1])
    whole = chr(10).join(lines)
    if whole.count(old_full) != 1: return None
    sig_brace = chr(10).join(lines[sig_idx:brace_idx + 1])
    new_body = sig_brace + chr(10) + '        ' + y + chr(10) + lines[end_idx]
    return {"name": f"ret-v3-{ln}", "old": old_full, "new": new_body, "line": ln}
