# Small input/output helpers: prompts with validation and table printing.

#Every prompt returns None when the user just presses Enter, which the menu
#code treats as "cancel / go back".
import textwrap


def ask_text(prompt, max_len=None):
    while True:
        value = input(prompt).strip()
        if not value:
            return None
        if max_len and len(value) > max_len:
            print(f"  Too long: {len(value)} characters (maximum {max_len}).")
            continue
        return value


def ask_int(prompt, minimum=None, maximum=None):
    while True:
        raw = input(prompt).strip()
        if not raw:
            return None
        try:
            value = int(raw)
        except ValueError:
            print("  Please enter a whole number.")
            continue
        if minimum is not None and value < minimum:
            print(f"  Must be at least {minimum}.")
        elif maximum is not None and value > maximum:
            print(f"  Must be at most {maximum}.")
        else:
            return value


def ask_choice(prompt, choices):
    """Ask for one of `choices` (single letters); returns lowercase letter or None."""
    while True:
        raw = input(prompt).strip().lower()
        if not raw:
            return None
        if raw in choices:
            return raw
        print(f"  Please enter one of: {', '.join(sorted(choices))}")


def confirm(prompt):
    return ask_choice(prompt + " [y/n]: ", {"y", "n"}) == "y"


def _fmt(value, max_width):
    text = "-" if value is None else str(value).replace("\n", " ")
    return text if len(text) <= max_width else text[: max_width - 3] + "..."


def print_table(rows, empty_message="No results.", max_width=60):
    if not rows:
        print(empty_message)
        return
    headers = rows[0].keys()
    cells = [[_fmt(row[h], max_width) for h in headers] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in cells)) for i, h in enumerate(headers)]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("  ".join("-" * w for w in widths))
    for r in cells:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))
    print(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")


def print_record(row):
    """Print one row as 'Label: value' lines."""
    width = max(len(k) for k in row.keys())
    for key in row.keys():
        print(f"  {key.ljust(width)} : {row[key]}")


def print_wrapped(text, indent="  "):
    print(textwrap.fill(text, width=78, initial_indent=indent, subsequent_indent=indent))