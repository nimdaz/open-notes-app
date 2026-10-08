"""Helpers for checklist notes, whose content is stored as one item per line:
"[x] done item" / "[ ] open item".
"""


def parse_items(content):
    """Return a list of (done, text) tuples."""
    items = []
    for line in (content or "").splitlines():
        if not line.strip():
            continue
        if line.startswith("[x] "):
            items.append((True, line[4:]))
        elif line.startswith("[ ] "):
            items.append((False, line[4:]))
        else:
            items.append((False, line.strip()))
    return items


def dump_items(items):
    return "\n".join(f"[{'x' if done else ' '}] {text}" for done, text in items)


def items_as_text(content):
    """Plain one-item-per-line text, as shown in the edit box."""
    return "\n".join(text for _, text in parse_items(content))


def merge_edited_text(old_content, edited_text):
    """Turn edited plain lines back into checklist content, keeping the checked
    state of items whose text did not change.
    """
    previous_states = {}
    for done, text in parse_items(old_content):
        previous_states.setdefault(text, []).append(done)

    items = []
    for line in (edited_text or "").splitlines():
        text = line.strip()
        if text:
            states = previous_states.get(text)
            items.append((states.pop(0) if states else False, text))
    return dump_items(items)
