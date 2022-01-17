##
# Copyright 2020 Palantir Technologies, Inc. All rights reserved.
# Licensed under the MIT License (the "License"); you may obtain a copy of the
# license at https://github.com/palantir/pyspark-style-guide/blob/develop/LICENSE
##


import astroid

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker

from pylint_utils import select_contains_alias_call


class SelectCastChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = 'select-cast'
    priority = -1
    msgs = {
        'E1076': (
            'Select statements should not contain .cast calls',
            'select-contains-cast',
            'Readability of select calls can be much improved by extracting .cast calls.'
        ),
    }

    def is_line_split(self, function):
        line = function.lineno
        for arg in function.args.args:
            if arg.lineno != line:
                return True
        return False

    def __init__(self, linter=None):
        super(SelectCastChecker, self).__init__(linter)
        self._function_stack = []

    def visit_functiondef(self, node):
        self._function_stack.append([])

    def visit_expr(self, node):
        if select_contains_alias_call(node):
            self.add_message('select-contains-cast', node=node)

    def leave_functiondef(self, node):
        self._function_stack.pop()
