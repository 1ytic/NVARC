import re
import tree_sitter_python
from tree_sitter import Language, Parser, Node

PY_LANGUAGE = Language(tree_sitter_python.language())

parser = Parser()
parser.language = PY_LANGUAGE

def get_value(match: dict[str, list[Node]], name: str) -> str:
    values = match[name]
    assert len(values) == 1
    return values[0].text.decode("utf8")

def parse_functions(text: str) -> dict[str, str]:
    query = PY_LANGUAGE.query(
        """
        (
            function_definition
            name: (identifier) @name
        ) @code
        """
    )
    names = dict()
    tree = parser.parse(bytes(text, "utf8"))
    for _, match in query.matches(tree.root_node):
        if match["code"][0].start_point.column != 0:
            # Exclude nested functions
            continue
        name = get_value(match, "name")
        code = get_value(match, "code")
        # assert name not in names, f"{name} already exists in {names.keys()}"
        names[name] = code
    return names

def clean_code(code):
    code = code.strip()
    # Remove if __name__ == "__main__":
    m = re.search(r"\n+if __name__", code, flags=re.DOTALL)
    if m:
        code = code[:m.start(0)].strip()
    # Remove last comment block or empty lines
    lines = code.strip().split("\n")
    new_lines = lines.copy()
    for line in reversed(lines):
        if line.startswith("#") or not line.strip():
            new_lines.pop()
        else:
            break
    code = "\n".join(new_lines).strip()
    return code

def remove_unused_functions(code: str) -> str:
    code = clean_code(code)
    functions = parse_functions(code)
    for function_name, function_code in functions.items():
        if function_name == "generate_puzzle_input":
            continue
        if function_name == "generate_puzzle_output":
            continue
        if function_name.startswith("test_"):
            continue
        usages = re.findall(re.escape(function_name) + r"\(", code)
        if len(usages) == 1:
            new_code = re.search(r".*(\n\n+.*)" + re.escape(function_code), code, flags=re.DOTALL)
            start = new_code.start(1)
            end = new_code.end(0)
            code = code[:start].strip() + code[end:]
    code = clean_code(code)
    return code

def parse_python_code(code: str):
    codes = re.findall(r"```python(.*?)```", code, re.DOTALL)
    if not codes:
        return None
    longest_code = max(codes, key=len)
    return longest_code.strip()