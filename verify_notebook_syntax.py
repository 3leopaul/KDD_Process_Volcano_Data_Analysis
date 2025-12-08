import json
import ast

def verify_notebook_syntax(notebook_path):
    print(f"Verifying syntax for: {notebook_path}")
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    error_count = 0
    
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if not source.strip(): continue
            
            try:
                ast.parse(source)
            except SyntaxError as e:
                print(f"Syntax error in cell {i}: {e}")
                print(f"Source snippet: {source[:100]}...")
                error_count += 1
            except Exception as e:
                print(f"Error parsing cell {i}: {e}")
                error_count += 1

    if error_count == 0:
        print("Verification Successful: No syntax errors found in notebook code cells.")
    else:
        print(f"Verification Failed: Found {error_count} syntax errors.")

if __name__ == "__main__":
    verify_notebook_syntax('main.ipynb')
