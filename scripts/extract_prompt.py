"""Copy a verbatim prompt block out of a prompt log: prompt_block(log_path, section_id) returns the text between the first line starting with ``` after the line "## <section_id>" and the next line that is exactly the opening fence (the run of backticks at the start of the opening line, three or four)."""

import sys
from pathlib import Path


def prompt_block(log_path, section_id):
    lines = Path(log_path).read_text(encoding="utf-8").splitlines()
    heading = "## " + section_id
    try:
        start = lines.index(heading)
    except ValueError:
        raise ValueError(f"section not found: {section_id}")
    block = []
    fence = None
    for line in lines[start + 1:]:
        if fence is None:
            if line.startswith("```"):
                fence = line[: len(line) - len(line.lstrip("`"))]
        elif line == fence:
            break
        else:
            block.append(line)
    if fence is None:
        raise ValueError(f"no prompt block found in section: {section_id}")
    return "\n".join(block)


def main():
    if len(sys.argv) != 3:
        print("usage: python scripts/extract_prompt.py <log_path> <section_id>", file=sys.stderr)
        sys.exit(2)
    print(prompt_block(sys.argv[1], sys.argv[2]))


if __name__ == "__main__":
    main()
