import sys
def foo(): a = 9/0
try:
    foo()
except Exception as err:
    sys.print_exception(err)

    

