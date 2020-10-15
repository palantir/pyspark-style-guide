##
# Copyright 2020 Palantir Technologies, Inc. All rights reserved.
# Licensed under the MIT License (the "License"); you may obtain a copy of the
# license at https://github.com/palantir/pyspark-style-guide/blob/develop/LICENSE
##


import astroid

from pylint import checkers
from pylint import interfaces


class ChainedDotFunctionsSyntaxChecker(checkers.BaseChecker):
    __implements__ = interfaces.IAstroidChecker

    name = 'chained-function-length'

    msgs = {
        'E1085': (
            'Chained functions applied on a variable should not be more than 3.',
            'chained-function-length',
            'Applied functions should not be more than 3 as it becomes difficult to follow.'
        ),
    }

    def visit_assign(self, node):
        depth = get_num_of_first_level_functions(node, 0)
        if depth > 3:
            self.add_message('chained-function-length', node=node)
        else:
            return


def get_num_of_first_level_functions(node, counter):
    if hasattr(node, 'value'):
        curr_value = node.value
        if isinstance(curr_value, astroid.Call):
            return get_num_of_first_level_functions(curr_value.func, counter+1)
    elif hasattr(node, 'expr'):
        curr_value = node.expr
        if isinstance(curr_value, astroid.Call):
            return get_num_of_first_level_functions(curr_value.func, counter+1)

    return counter
