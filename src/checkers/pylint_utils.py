##
# Copyright 2020 Palantir Technologies, Inc. All rights reserved.
# Licensed under the MIT License (the "License"); you may obtain a copy of the
# license at https://github.com/palantir/pyspark-style-guide/blob/develop/LICENSE
##

import astroid


def compute_arguments_length(arguments):
    args_length = 0
    for arg in arguments:
        args_length += get_length(arg)
    return args_length


def compute_target_lengths(targets):
    total_length = 0
    for target in targets:
        total_length += get_length(target)
    return total_length


def select_contains_alias_call(expression):
    if not hasattr(expression.value.func, 'attrname'):
        return False
    if expression.value.func.attrname == 'select':
        for arg in expression.value.args:
            if isinstance(arg, astroid.nodes.Call):
                if arg.func.attrname == 'alias':
                    return True
    return False

def select_contains_cast_call(expression):
    if not hasattr(expression.value.func, 'attrname'):
        return False
    if expression.value.func.name == 'select':
        for arg in expression.value.args:
            if isinstance(arg, astroid.nodes.Call):
                if arg.func.attrname == 'cast':
                    return True
    return False

def is_line_split(val):
    line = val.lineno
    if isinstance(val, astroid.nodes.Function):
        for arg in val.args.args:
            if arg.lineno != line:
                return True
        return False
    if isinstance(val, astroid.nodes.Call):
        for arg in val.args:
            if arg.lineno != line:
                return True
        return False
    if isinstance(val, astroid.nodes.Assign):
        if hasattr(val.value, 'args'):
            for arg in val.value.args: 
                if arg.lineno != line:
                    return True
        if hasattr(val.value, 'elts'):
            for arg in val.value.elts:
                if arg.lineno != line:
                    return True
        return False

def get_binary_op_complexity(arg):
    if isinstance(arg, astroid.nodes.BinOp):
        nested_complexity = get_binary_op_complexity(arg.left) + get_binary_op_complexity(arg.right)
        # We need this Because essentially multiple ops are nested
        return 1 + (nested_complexity if nested_complexity > 0 else 1)
    return 0

def get_length(arg):
    if isinstance(arg, astroid.nodes.Const):
        length = len(str(arg.value))
        if isinstance(arg.pytype(), basestring):
            length += 2  # Quotes
        return length
    if isinstance(arg, astroid.nodes.BinOp):
        base_length = 3  # _+_
        compound_length = get_length(arg.left) + get_length(arg.right)
        #print "Binop length %d" % (compound_length)
        return base_length + compound_length
    if isinstance(arg, astroid.nodes.Call):
        #print arg
        base_length = 2  # Open and closing brackets
        length = get_length(arg.func) + \
            compute_arguments_length(arg.args) + base_length
        #print "Call length %s" % length
        return length
    if isinstance(arg, astroid.nodes.Attribute):
        base_length = 1  # Period
        if hasattr(arg.expr, 'name'):
            expr_length = len(arg.expr.name)
        else:
            expr_length = get_length(arg.expr)
        total_length = expr_length + base_length + len(arg.attrname)
        return total_length
    if isinstance(arg, astroid.nodes.Assign):
        # print arg
        base_length = 2  # Brackets
        target_length = compute_target_lengths(arg.targets)
        value_length = get_length(arg.value)
        return base_length + value_length + target_length
    if isinstance(arg, astroid.nodes.Tuple):
        args_length = 0
        for value in arg.elts:
            args_length += len(value.name)
        if len(arg.elts) > 1:
            args_length += ((len(arg.elts) - 1) * 2)
        return args_length
    if isinstance(arg, astroid.nodes.Name):
        return len(arg.name)
    if isinstance(arg, astroid.nodes.AssignName):
        return len(arg.name)
    if isinstance(arg, astroid.nodes.Compare):
        total_length = 0
        for op in arg.ops:
            total_length += 2 + len(op[0]) + get_length(op[1])
        total_length += get_length(arg.left)
        return total_length
    if isinstance(arg, astroid.nodes.List):
        total_length = 0
        for value in arg.elts:
            total_length += get_length(value)
        return total_length
    print "Unhandled %s" % arg
    return 0
