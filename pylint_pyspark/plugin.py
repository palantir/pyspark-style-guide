from pyspark_style_guide.checkers import register as register_checkers

def register(linter):
    register_checkers(linter)
