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


class StatementCallChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = 'split-statement'
    priority = -1
    msgs = {
        'E1073': (
            'Statements should be on a single line if they fit.',
            'unnecessarily-split-statement',
            'This statement fits into a single line and as such should not be split across multiple lines.'
        ),
    }

    def is_line_split(self, function):
        line = function.lineno
        for arg in function.args.args:
            if arg.lineno != line:
                return True
        return False

    def __init__(self, linter=None):
        super(StatementCallChecker, self).__init__(linter)
        self._function_stack = []

    def visit_functiondef(self, node):
        self._function_stack.append([])

    def visit_assign(self, node):
        if is_line_split(node):
            base_length = 3  # _=_
            if get_length(node) + base_length <= 120:
                self.add_message(
                    'unnecessarily-split-statement', node=node)

    def leave_functiondef(self, node):
        self._function_stack.pop()
