
import pytest

from tibanna_ffcommon.misc_utils import (
    LogicalExpressionParser
)

def test_logical_expression_parser():

    LEP = LogicalExpressionParser("True")
    assert LEP.evaluate() == True

    LEP = LogicalExpressionParser("False")
    assert LEP.evaluate() == False

    LEP = LogicalExpressionParser("True and False")
    assert LEP.evaluate() == False

    LEP = LogicalExpressionParser("True and True")
    assert LEP.evaluate() == True

    LEP = LogicalExpressionParser("True or False")
    assert LEP.evaluate() == True

    LEP = LogicalExpressionParser("(True or False) and True")
    assert LEP.evaluate() == True

    LEP = LogicalExpressionParser("not (True or False) and True")
    assert LEP.evaluate() == False

    LEP = LogicalExpressionParser("not (True or False) or False")
    assert LEP.evaluate() == False

    LEP = LogicalExpressionParser("not (True or False) or not False")
    assert LEP.evaluate() == True

    LEP = LogicalExpressionParser("not (not (not True))")
    assert LEP.evaluate() == False


def test_logical_expression_parser_invalid_input():
    with pytest.raises(Exception, match="Unsupported token: 2"):
       LEP = LogicalExpressionParser("2")
       LEP.evaluate()

    with pytest.raises(Exception, match="Unsupported token: ."):
       LEP = LogicalExpressionParser("True and True.")
       LEP.evaluate()
    