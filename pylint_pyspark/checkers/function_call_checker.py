##
# Copyright 2020 Palantir Technologies, Inc. All rights reserved.
# Licensed under the MIT License (the "License"); you may obtain a copy of the
# license at https://github.com/palantir/pyspark-style-guide/blob/develop/LICENSE
##

import astroid

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker

from pylint_utils import compute_arguments_length
from pylint_utils import is_line_split
from pylint_utils import get_length


class FunctionCallChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = 'split-call'
    priority = -1
    msgs = {
        'E1072': (
            'Function call arguments should be on the same line if they fit.',
            'unnecessarily-split-call',
            'All arguments for this function fit into a single line and as such should be in a single line'
        ),
    }

    def is_line_split(self, function):
        line = function.lineno
        for arg in function.args.args:
            if arg.lineno != line:
                return True
        return False

    def __init__(self, linter=None):
        super(FunctionCallChecker, self).__init__(linter)
        self._function_stack = []

    def visit_functiondef(self, node):
        for statement in node.body:
            if isinstance(statement, astroid.nodes.Expr):
                if is_line_split(statement.value):
                    args_length = compute_arguments_length(
                        statement.value.args)
                    total_length = len(statement.value.func.name) + \
                        statement.col_offset + args_length
                    if total_length <= 120:
                        self.add_message('unnecessarily-split-call', node=node)
        self._function_stack.append([])

    def leave_functiondef(self, node):
        self._function_stack.pop()

    def visit_functionheadercorrect(self, node):
        return
