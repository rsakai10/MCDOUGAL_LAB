import re
import os
import pathlib

def convert_tabs_to_spaces(text_with_tabs: str, tab_stop: int = 8) -> str:
    """
    Converts tabs in a string to spaces, aligning them to the next multiple of the tab_stop.

    Args:
        text_with_tabs: The input string which may contain tabs.
        tab_stop: The number of spaces a tab represents, and to which columns
                  are aligned (e.g., 8 for standard tab stops).

    Returns:
        A new string with tabs replaced by the appropriate number of spaces.
    """
    if not isinstance(text_with_tabs, str):
        raise TypeError("Input 'text_with_tabs' must be a string.")
    if not isinstance(tab_stop, int) or tab_stop <= 0:
        raise ValueError("Input 'tab_stop' must be a positive integer.")

    converted_text = []
    current_column = 0

    for char in text_with_tabs:
        if char == '\t':
            # Calculate how many spaces are needed to reach the next tab stop
            spaces_needed = tab_stop - (current_column % tab_stop)
            if spaces_needed == 0:
                # If already at a tab stop, a tab still moves to the *next* one
                spaces_needed = tab_stop
            converted_text.append(' ' * spaces_needed)
            current_column += spaces_needed
        elif char == '\n':
            # Reset column count for new line
            converted_text.append(char)
            current_column = 0
        else:
            # Append regular character and increment column count
            converted_text.append(char)
            current_column += 1

    return "".join(converted_text)

def read_lines(filename, tab_stop=8):
    with open(str(filename), encoding="utf-8") as f:
        return [convert_tabs_to_spaces(line.rstrip("\n"), tab_stop) for line in f]
    
def extract_blocks_with_parse_rst_style(lines, kinds=None):
    if kinds is None:
        kinds = ["hoc:method", "hoc:data", "hoc:class", "hoc:function", "index"]
    blocks = []
    i = 0
    while i < len(lines):
        found = False
        for kind in kinds:
            identifier = ".. %s::" % kind
            line = lines[i]
            start = line.find(identifier)
            if start >= 0:
                name = line[start + len(identifier):].strip()
                indent_line = lines[i + 1]
                while not indent_line.strip():
                    i += 1
                    indent_line = lines[i + 1]
                start_indent = len(indent_line) - len(indent_line.lstrip())
                body = []
                while i < len(lines) - 1:
                    i += 1
                    if lines[i].strip():
                        if lines[i].startswith(" " * start_indent):
                            body.append(lines[i][start_indent:])
                        else:
                            break
                    else:
                        if not body or body[-1] != "\n":
                            body.append("\n")
                blocks.append((kind, name, "\n".join(body)))
                found = True
                break
        if not found:
            i += 1
    return blocks


def merge_by_indent(py_lines, hoc_blocks, out_path):
    merged = []
    hoc_dict = {name: (kind, doc) for kind, name, doc in hoc_blocks}
    i = 0

    pattern = re.compile(r"\s*\.\. (class|method|data|function|index)::\s+([A-Za-z0-9_.]+)")

    while i < len(py_lines):
        line = py_lines[i]
        merged.append(line + "\n")

        match = pattern.match(line)
        if match:
            kind, name = match.groups()
            merged.append("\n    .. tab:: Python\n")

            # Skip blank lines and copy indented lines
            i += 1
            while i < len(py_lines) and not py_lines[i].strip():
                merged.append("     " + py_lines[i] + "\n")
                i += 1

            if i < len(py_lines):
                indent = len(py_lines[i]) - len(py_lines[i].lstrip())
            else:
                indent = 0

            while i < len(py_lines):
                if py_lines[i].strip() == "":
                    merged.append(py_lines[i] + "\n")
                    i += 1
                    continue
                this_indent = len(py_lines[i]) - len(py_lines[i].lstrip())
                if this_indent >= indent and py_lines[i].startswith(" " * indent):
                    merged.append("    " + py_lines[i] + "\n")
                    i += 1
                else:
                    break

            # Insert matching HOC block if available
            if name in hoc_dict:
                _, hoc_doc = hoc_dict[name]
                merged.append("    .. tab:: HOC\n\n\n")
                for hoc_line in hoc_doc.splitlines():
                    merged.append("        " + hoc_line.replace(":hoc:", ":") + "\n")
        else:
            i += 1

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(merged)

# Directory paths
hoc_dir = "rst_hoc/has_hoc_directives"
py_dir = "rst_python"
out_dir = "unified_docs"

for p in pathlib.Path(hoc_dir).rglob('*'):
    if p.is_file() and p.name.endswith(".rst"):
        file = p.stem  # Extract just the file name without extension
        py_path = os.path.join(py_dir, f"{file}.rst")
        hoc_path = str(p)
        out_path = os.path.join(out_dir, f"{file}_merged.rst")
        if os.path.exists(out_path):
            print(f"Skipped (already exists): {file}_merged.rst")
            continue
        if os.path.exists(py_path):
            py_read_lines = read_lines(py_path)
            hoc_read_lines = read_lines(hoc_path)
            hoc_blocks = extract_blocks_with_parse_rst_style(hoc_read_lines)
            merge_by_indent(py_read_lines, hoc_blocks, out_path)
            print(f"Merged: {file}")
        else:
            print(f"Python file not found for: {file}")

