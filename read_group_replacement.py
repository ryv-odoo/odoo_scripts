import sys
import os
import ast
from typing import Any

include_type = '.py'

empty_list = ast.parse("[]").body[0].value

class AbstractVisitor(ast.NodeVisitor):

    def __init__(self) -> None:
        # ((line, line_end, col_offset, end_col_offset), replace_by) NO OVERLAPS
        self.change_todo = []

    def post_process(self, all_code:str) -> str:
        all_lines = all_code.split('\n')
        for (lineno, line_end, col_offset, end_col_offset), new_substring in sorted(self.change_todo, reverse=True):
            if lineno == line_end:
                line = all_lines[lineno - 1]
                all_lines[lineno - 1] = line[:col_offset] + new_substring + line[end_col_offset:]
            else:
                raise ValueError("Error")
        return '\n'.join(all_lines)

    def add_change(self, old_node: ast.AST, new_node: ast.AST | str):
        position = (old_node.lineno, old_node.end_lineno, old_node.col_offset, old_node.end_col_offset)
        if isinstance(new_node, str):
            self.change_todo.append((position, new_node))
        else:
            self.change_todo.append((position, ast.unparse(new_node)))


class VisitorToPrivateReadGroup(AbstractVisitor):

    def post_process(self, all_code:str) -> str:
        all_lines = all_code.split('\n')
        for i, line in enumerate(all_lines):
            if 'super(' not in line:
                all_lines[i] = line.replace('.read_group(', '._read_group(')
        return '\n'.join(all_lines)


class VisitorInverseGroupbyFields(AbstractVisitor):

    def visit_Call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Attribute) and node.func.attr == '_read_group':
            # Should have the same number of args/keywords
            # Inverse fields/groupby order
            keywords_by_key = {keyword.arg: keyword.value for keyword in node.keywords}
            key_i_by_key = {keyword.arg: i for i, keyword in enumerate(node.keywords)}
            if len(node.args) >= 3:
                self.add_change(node.args[2], node.args[1])
                self.add_change(node.args[1], node.args[2])
            elif len(node.args) == 2:
                new_args_value = keywords_by_key.get('groupby', empty_list)
                if 'groupby' in keywords_by_key:
                    fields_args = ast.keyword('fields', node.args[1])
                    self.add_change(node.args[1], new_args_value)
                    self.add_change(node.keywords[keywords_by_key['groupby']], fields_args)
                else:
                    self.add_change(node.args[1], f'{ast.unparse(new_args_value)}, {ast.unparse(node.args[1])}')
            else:  # len(node.args) <= 2
                if 'groupby' in key_i_by_key and 'fields' in key_i_by_key:
                    if key_i_by_key['groupby'] < key_i_by_key['fields']:
                        self.add_change(node.keywords[key_i_by_key['groupby']], node.keywords[key_i_by_key['fields']])
                        self.add_change(node.keywords[key_i_by_key['fields']], node.keywords[key_i_by_key['groupby']])
                else:
                    raise ValueError(f"{key_i_by_key}, {keywords_by_key}, {node.args}")
        self.generic_visit(node)


class VisitorRenameKeywords(AbstractVisitor):

    def visit_Call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Attribute) and node.func.attr == '_read_group':
            # Replace fields by aggregate and orderby by order
            for keyword in node.keywords:
                if keyword.arg == 'fields':
                    new_keyword = ast.keyword('aggregates', keyword.value)
                    self.add_change(keyword, new_keyword)
                if keyword.arg == 'orderby':
                    new_keyword = ast.keyword('order', keyword.value)
                    self.add_change(keyword, new_keyword)
        self.generic_visit(node)


class VisitorRemoveLazy(AbstractVisitor):

    def post_process(self, all_code):
        # remove extra comma ',' and extra line if possible
        all_code = super().post_process(all_code)
        all_lines = all_code.split('\n')
        for (lineno, __, col_offset, __), __ in sorted(self.change_todo, reverse=True):
            comma_find = False
            line = all_lines[lineno - 1]
            remaining = line[col_offset:]
            line = line[:col_offset]
            while not comma_find:
                if ',' not in line:
                    all_lines.pop(lineno - 1)
                    lineno -= 1
                    line = all_lines[lineno - 1]
                else:
                    comma_find = True
            last_index_comma = - (line[::-1].index(',') + 1)
            all_lines[lineno - 1] = line[:last_index_comma] + remaining

        return '\n'.join(all_lines)

    def visit_Call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Attribute) and node.func.attr == '_read_group':
            # Replace fields by aggregate and orderby by order
            if len(node.args) == 7:
                self.add_change(node.args[6], '')
            else:
                for keyword in node.keywords:
                    if keyword.arg == 'lazy':
                        self.add_change(keyword, '')
        self.generic_visit(node)


class VisitorAggregatesSpec(AbstractVisitor):

    def visit_Call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Attribute) and node.func.attr == '_read_group':

            keywords_by_key = {keyword.arg: keyword.value for keyword in node.keywords}
            aggregate_values = None
            if len(node.args) >= 3:
                aggregate_values = node.args[2]
            elif 'aggregates' in keywords_by_key:
                aggregate_values = keywords_by_key['aggregates']

            groupby_values = empty_list
            if len(node.args) >= 2:
                groupby_values = node.args[1]
            elif 'groupby' in keywords_by_key:
                groupby_values = keywords_by_key['groupby']

            if aggregate_values:
                aggregates = None
                try:
                    aggregates = ast.literal_eval(ast.unparse(aggregate_values))
                    if not isinstance(aggregates, (list, tuple)):
                        raise ValueError(f"{aggregate_values} is not a list but literal ?")

                    aggregates = [
                        f"{field_spec.split('(')[1][:-1]}:{field_spec.split(':')[1].split('(')[0]}" if '(' in field_spec else field_spec
                        for field_spec in aggregates
                    ]
                    aggregates = [
                        '__count' if field_spec in ('id:count', 'id:count_distinct') else field_spec
                        for field_spec in aggregates
                    ]

                    groupby = ast.literal_eval(ast.unparse(groupby_values))
                    if isinstance(groupby, str):
                        groupby = [groupby]

                    aggregates = [
                        f'{field}:sum' if (':' not in field and field != '__count') else field
                        for field in aggregates if field not in groupby
                    ]
                    if not aggregates:
                        aggregates = ['__count']
                except SyntaxError:
                    pass
                except ValueError:
                    pass

                if aggregates is not None:
                    self.add_change(aggregate_values, repr(aggregates))
        self.generic_visit(node)


Steps_visitor: list[AbstractVisitor] = [
    VisitorToPrivateReadGroup,
    VisitorInverseGroupbyFields,
    VisitorRenameKeywords,
    VisitorAggregatesSpec,
    VisitorRemoveLazy,
]


def replace_read_group_signature(filename):
    with open(filename, mode='rt') as file:
        new_all = all_code = file.read()
        if 'read_group' in all_code:
            for Step in Steps_visitor:
                visitor = Step()
                try:
                    visitor.visit(ast.parse(new_all))
                except Exception:
                    print(f"ERROR in {filename} at step {visitor.__class__}: \n{new_all}")
                    raise
                new_all = visitor.post_process(new_all)

    if new_all != all_code:
        print('Write, ', filename)
        with open(filename, mode='wt') as file:
            file.write(new_all)

ignore_files = """
account_accountant/models/bank_rec_widget.py
account_accountant/models/digest.py
account_asset/models/account_asset.py
account_consolidation/models/consolidation_journal.py
account_consolidation/models/consolidation_period.py
account_consolidation/report/builder/comparison.py
account_consolidation/report/builder/default.py
account_disallowed_expenses/report/account_disallowed_expenses_report.py
account_disallowed_expenses_fleet/report/account_disallowed_expenses_report.py
account_followup/models/res_partner.py
""".strip().split('\n')

regex_dict = r"""
\{[\s\n]*\w+\[["'](.+)(?:_id)["']\](?:\[0\])?[\s\n]*:[\s\n]*\w+\[.*?([a-zA-Z]+)["']\](\s+for\s+)\w+(\s+in\s+\w+[\s\n]*)\}
"""

# {$1.id: $2$3$1, $2$4}

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
    print(f"Change _read_group in {directories_to_check}")
    for directory in directories_to_check:
        if os.path.isdir(directory):
            walk_directory(directory)
        elif os.path.isfile(directory):
            replace_read_group_signature(directory)
