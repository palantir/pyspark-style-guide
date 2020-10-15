from function_call_checker import FunctionCallChecker
from logic_op_complexity_checker import LogicOpComplexityChecker
from select_alias_checker import SelectAliasChecker
from select_cast_checker import SelectCastChecker
from statement_call_checker import StatementCallChecker
from chained_function_checker import ChainedDotFunctionsSyntaxChecker

def register(linter):
    linter.register_checker(FunctionCallChecker(linter))
    linter.register_checker(LogicOpComplexityChecker(linter))
    linter.register_checker(SelectAliasChecker(linter))
    linter.register_checker(SelectCastChecker(linter))
    linter.register_checker(StatementCallChecker(linter))
    linter.register_checker(ChainedDotFunctionsSyntaxChecker(linter))