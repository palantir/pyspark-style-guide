##
# Copyright 2020 Palantir Technologies, Inc. All rights reserved.
# Licensed under the MIT License (the "License"); you may obtain a copy of the
# license at https://github.com/palantir/pyspark-style-guide/blob/develop/LICENSE
##

import astroid

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker

from pylint_utils import get_binary_op_complexity



class LogicOpComplexityChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = 'logic-op-complexity'
    priority = -1
    msgs = {
        'E1074': (
            'Complexity of inline logic statement should be 3 or lower.',
            'high-logic-op-complexity',
            'This statement has a high complexity and should be split into several smaller statements assigned with descriptive variable names.'
        ),
    }

    def is_line_split(self, function):
        line = function.lineno
        for arg in function.args.args:
            if arg.lineno != line:
                return True
        return False

    def __init__(self, linter=None):
        super(LogicOpComplexityChecker, self).__init__(linter)
        self._function_stack = []

    def visit_functiondef(self, node):
        self._function_stack.append([])

    def visit_binop(self, node):
        if get_binary_op_complexity(node) > 3:
            self.add_message('high-logic-op-complexity', node=node)

    def leave_functiondef(self, node):
        self._function_stack.pop()
