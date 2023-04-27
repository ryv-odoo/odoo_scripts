


import ast
import os
import sys
import re

from typing import Any

import subprocess

class AbstractVisitor(ast.NodeVisitor):

    def __init__(self, all_code) -> None:
        # ((line, line_end, col_offset, end_col_offset), replace_by) NO OVERLAPS
        self.all_code = all_code
        self.change_todo = []

    def post_process(self, all_code:str, file:str) -> str:
        for (old_str, new_str) in self.change_todo:
            all_code = all_code.replace(old_str, new_str)
        return all_code

    def add_change(self, old_str, new_str):
        print()

        # Add ruff auto fix
        # ['/home/odoo/Documents/dev/.env/bin/ruff', '--force-exclude', '--no-cache', '--fix', '--stdin-filename', '/home/odoo/Documents/dev/odoo_scripts/regex_name_get.py']

        result = subprocess.run(
            ['ruff', '-', '--fix', '--stdin-filename', '<part_of_file>', '--select=ALL', '--ignore=D211,D213,Q,D'],
            stdout=subprocess.PIPE,
            input=new_str.encode('utf-8'),
        )
        new_str_ruff = result.stdout.decode('utf-8')

        print("OLD:")
        print(old_str)
        print("NEW:")
        print(new_str)
        print("After RUFF:")
        print(new_str_ruff)

        self.change_todo.append((old_str, "    " + new_str_ruff))

# [(batch.id, f'{batch.name} ({state_values.get(batch.state)})') for batch in self]
list_comprehension_re = re.compile(r"""def name_get\(self\):(.*)
        return \[\s*\(.*id,\s*(.+)\s*\)\s*for\s*(\w+)\s*in\s*self\s*\]""", re.S)
list_comprehension_into = r"""def _compute_display_name(self):\g<1>
        for \g<3> in self:
            \g<3>.display_name = \g<2>"""

# res = []
# for wo in self:
#     if len(wo.production_id.workorder_ids) == 1:
#         res.append((wo.id, "%s - %s - %s" % (wo.production_id.name, wo.product_id.name, wo.name)))
#     else:
#         res.append((wo.id, "%s - %s - %s - %s" % (wo.production_id.workorder_ids.ids.index(wo._origin.id) + 1, wo.production_id.name, wo.product_id.name, wo.name)))
# return res


list_append_re = re.compile(r"""def name_get\(self\):.+
        return ([A-Za-z_]+)""", re.S)

class VisitorNameGet(AbstractVisitor):

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        if node.name == 'name_get':
            # Replace fields by aggregate and orderby by order
            code = ast.get_source_segment(self.all_code, node)
            new_code = list_comprehension_re.sub(list_comprehension_into, code, 1)
            if new_code != code:
                self.add_change(code, new_code)
            elif groups := list_append_re.fullmatch(new_code):
                variable_to_remove = groups.group(1)
                new_code = new_code.replace(f"\n        {variable_to_remove} = []", "")
                new_code = new_code.replace("def name_get(self):", "def _compute_display_name(self):")
                new_code = new_code.replace("super().name_get()", "super()._compute_display_name()")
                new_code = new_code.replace(f"\n        return {variable_to_remove}", "")
                new_code = re.sub(variable_to_remove + r".append\(\((.+).id, (.*),?\)\)", r"\g<1>.display_name = \g<2>", new_code)
                self.add_change(code, new_code)
            else:
                print(f"Cannot find a way to convert:\n{code}")

        # self.generic_visit(node)

ignore_files = """
/home/odoo/Documents/dev/odoo/odoo/models.py
""".strip().split('\n')
ignore_files = [ignore for ignore in ignore_files if ignore]

Steps_visitor: list[AbstractVisitor] = [
    VisitorNameGet,
]

def replace_read_group_signature(filename):
    with open(filename) as file:
        new_all = all_code = file.read()
        if 'def name_get(' in all_code:
            for Step in Steps_visitor:
                visitor = Step(all_code)
                try:
                    visitor.visit(ast.parse(new_all))
                except Exception:
                    print(f"ERROR in {filename} at step {visitor.__class__}: \n{new_all}")
                    raise
                new_all = visitor.post_process(new_all, filename)
            if new_all == all_code:
                print('name_get detected but not changed', filename)

    if new_all != all_code:
        print('Write, ', filename)
        with open(filename, mode="w") as file:
            file.write(new_all)

include_type = '.py'

def walk_directory(directory):
    for (dirpath, __, filenames) in os.walk(directory):
        for name in filenames:
            if not name.endswith(include_type):
                continue
            complete_path = os.path.join(dirpath, name)
            if any(ignore in complete_path for ignore in ignore_files):
                print('ignore: ', complete_path)
                continue
            replace_read_group_signature(complete_path)

if __name__ == '__main__':
    directories_to_check = sys.argv[1:]
    print(f"Change name_get in {directories_to_check}, nb ignore_files:{len(ignore_files)}")
    for directory in directories_to_check:
        if os.path.isdir(directory):
            walk_directory(directory)
        elif os.path.isfile(directory):
            replace_read_group_signature(directory)
