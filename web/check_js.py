"""Deep JS brace analysis."""
js = open('static/js/app.js', 'r', encoding='utf-8').read()

depth = 0
in_single = False
in_double = False
in_template = False
in_line_comment = False
in_block_comment = False
i = 0
last_depth_zero = 0
problems = []

while i < len(js):
    c = js[i]
    prev = js[i-1] if i > 0 else ''
    c2 = js[i:i+2] if i+1 < len(js) else ''

    # Track comments (only when not in a string)
    if not in_single and not in_double and not in_template:
        if c2 == '//' and not in_block_comment:
            in_line_comment = True
            i += 2
            continue
        if c2 == '/*' and not in_line_comment:
            in_block_comment = True
            i += 2
            continue
        if c == '\n':
            in_line_comment = False
        if c2 == '*/':
            in_block_comment = False
            i += 2
            continue
        if in_line_comment or in_block_comment:
            i += 1
            continue

    # Track strings
    if prev != '\\':
        if c == "'" and not in_double and not in_template:
            in_single = not in_single
        elif c == '"' and not in_single and not in_template:
            in_double = not in_double
        elif c == '`' and not in_single and not in_double:
            in_template = not in_template

    # Track braces outside strings
    if not in_single and not in_double and not in_template:
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth < 0:
                line = js[:i].count('\n') + 1
                problems.append(f'Line {line}: Extra closing brace (depth went negative)')
                depth = 0
            if depth == 0:
                last_depth_zero = i

    i += 1

if depth > 0:
    line = js[:last_depth_zero].count('\n') + 1
    problems.append(f'Line ~{line}: Unclosed brace(s), depth {depth}')
    # Show context
    lines = js[:last_depth_zero].split('\n')
    start = max(0, len(lines) - 8)
    print(f'Context around last depth=0 (line {len(lines)}):')
    for j in range(start, len(lines)):
        print(f'  {j+1}: {lines[j][:150]}')

if problems:
    print(f'\n{len(problems)} issues:')
    for p in problems:
        print(f'  {p}')
else:
    print(f'No issues. Final depth={depth}')
