import subprocess
import difflib
import sys
import re
from pathlib import Path

def get_git_version(filepath: str, revision: str = "HEAD~1") -> str:
    """Get the content of a file from a previous Git revision."""
    result = subprocess.run(
        ["git", "show", f"{revision}:{filepath}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,  # get raw bytes
    )
    if result.returncode != 0:
        raise Exception(f"Error fetching git version: {result.stderr.decode('utf-8', errors='ignore')}")
    return result.stdout.decode('utf-8', errors='ignore')

def get_current_version(filepath: str) -> str:
    """Read the current version of the file (UTF-8-safe)."""
    return Path(filepath).read_text(encoding="utf-8")

def extract_docstring_blocks(lines):
    """Extracts (start_line, end_line, block) for triple-quoted docstrings."""
    doc_blocks = []
    in_docstring = False
    docstring_delim = None
    start_index = 0
    current_block = []

    for i, line in enumerate(lines):
        if not in_docstring:
            if match := re.match(r'^[ \t]*[ruRU]*("""|\'\'\')', line):
                in_docstring = True
                docstring_delim = match.group(1)
                start_index = i
                current_block = [line]
                if line.strip().endswith(docstring_delim) and line.strip() != docstring_delim:
                    # one-liner docstring
                    doc_blocks.append((start_index, i, current_block.copy()))
                    in_docstring = False
        else:
            current_block.append(line)
            if line.strip().endswith(docstring_delim):
                doc_blocks.append((start_index, i, current_block.copy()))
                in_docstring = False
    return doc_blocks

def restore_comments(old_code: str, new_code: str) -> str:
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    sm = difflib.SequenceMatcher(None, old_lines, new_lines)
    restored_lines = []
    opcodes = sm.get_opcodes()

    # Extract docstring blocks from old code
    old_doc_blocks = extract_docstring_blocks(old_lines)
    doc_block_lines = {i for start, end, block in old_doc_blocks for i in range(start, end + 1)}

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            restored_lines.extend(new_lines[j1:j2])
        elif tag == "replace":
            old_block = old_lines[i1:i2]
            new_block = new_lines[j1:j2]
            merged_block = []

            old_index = 0
            new_index = 0
            while old_index < len(old_block) and new_index < len(new_block):
                old_line = old_block[old_index]
                new_line = new_block[new_index]

                # Check for inline comment loss
                if '#' in old_line and not old_line.strip().startswith('#'):
                    old_code_only = old_line.split('#')[0].rstrip()
                    new_code_only = new_line.rstrip()

                    if old_code_only == new_code_only and '#' not in new_line:
                        # Merge inline comment
                        comment = old_line.split('#', 1)[1].strip()
                        merged_line = f"{new_line}  # {comment}"
                        print(f"💬 Restoring inline comment on: {old_code_only}")
                        merged_block.append(merged_line)
                        old_index += 1
                        new_index += 1
                        continue

                merged_block.append(new_line)
                old_index += 1
                new_index += 1

            # Add any leftover lines (usually safe fallback)
            merged_block.extend(new_block[new_index:])
            restored_lines.extend(merged_block)

        elif tag == "delete":
            # Restore standalone full-line comments from deleted lines,
            # preserving blank line before if present in old code
            for i in range(i1, i2):
                line = old_lines[i]
                stripped = line.strip()
                if stripped.startswith("#"):
                    # Check for blank line before comment in old code
                    if i > 0 and old_lines[i - 1].strip() == "":
                        print(f"📌 Restoring blank line before comment at line {i}")
                        restored_lines.append("")  # blank line
                    print(f"📌 Restoring full-line comment: {stripped}")
                    restored_lines.append(line)

        elif tag == "insert":
            restored_lines.extend(new_lines[j1:j2])

    return "\n".join(restored_lines)

def restore_docstrings_missing_in_new(old_lines, new_lines):
    """Restore docstrings that are completely missing from the new version."""
    old_doc_blocks = extract_docstring_blocks(old_lines)
    new_text = "\n".join(new_lines)

    insertions = []

    for start, end, block in old_doc_blocks:
        # Look *above* docstring for def/class anchor
        anchor_line = ""
        for i in reversed(range(0, start)):
            anchor_candidate = old_lines[i].strip()
            if anchor_candidate.startswith(("def ", "class ")):
                anchor_line = anchor_candidate
                break

        if not anchor_line:
            continue  # no anchor found

        docstring_text = "\n".join(block).strip()
        if docstring_text not in new_text and anchor_line in new_text:
            print(f"🧩 Restoring missing docstring after: `{anchor_line}`")
            insertions.append((anchor_line, block))

    result_lines = []
    i = 0
    while i < len(new_lines):
        line = new_lines[i]
        stripped = line.strip()
        result_lines.append(line)

        # Insert docstring block immediately after anchor line
        for anchor, block in insertions[:]:  # iterate over a copy
            if stripped == anchor:
                result_lines.extend(block)
                insertions.remove((anchor, block))
                break
        i += 1

    return result_lines

def write_restored_file(filepath: str, restored_code: str):
    # Overwrite file directly, no backup
    Path(filepath).write_text(restored_code, encoding="utf-8")
    print(f"\n✅ Restored file written to {filepath}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python reverse_remove_comments.py <file.py>")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"🔍 Restoring comments in: {filepath}")

    old_code = get_git_version(filepath)
    new_code = get_current_version(filepath)
    
    # Phase 1: Restore inline + block comments
    partially_restored = restore_comments(old_code, new_code)
    
    # Phase 2: Restore docstrings by matching code anchors
    restored_lines = restore_docstrings_missing_in_new(
        old_code.splitlines(),
        partially_restored.splitlines()
    )

    final_code = "\n".join(restored_lines) + "\n"
    write_restored_file(filepath, final_code)

if __name__ == "__main__":
    main()
