from collections import deque

class LogicalExpressionParser:
    def __init__(self, expression: str):
        """Class that contains functions to evaluate a logical expression string.

        Args:
            expression (str): Logical expression string. E.g., "True and not (False or not True)"
        """
        # Convert to internal representation
        self.expression = (
            expression.lower()
            .replace("and", "&")
            .replace("or", "|")
            .replace("not", "1!")
            .replace("false", "f")
            .replace("true", "t")
            .replace(" ", "")
        )

    def evaluate(self) -> bool:
        """Evalutes a logical expression string. Supported operators 'and', 'or' and 'not', 
        e.g., "True and not (False or not True)"

        Returns:
            bool: value of evaluated expression
        """
        pf = self.infix_to_postfix(self.expression)
        return self.eval_postfix(pf)

    def infix_to_postfix(self, expression):
        operators = {"|": 1, "&": 2, "!": 3}  # sorted by operator precendence
        stack = []
        output = []

        for token in expression:
            if token in ["f", "t", "1"]:
                output.append(token)
            elif token == "(":
                stack.append(token)
            elif token == ")":
                while stack and stack[-1] != "(":
                    output.append(stack.pop())
                stack.pop()  # Discard the opening parenthesis
            elif token in operators.keys():
                while stack and operators.get(token, 0) <= operators.get(stack[-1], 0):
                    output.append(stack.pop())
                stack.append(token)
            else:
                raise Exception(f"Unsupported token: {token}")

        while stack:
            output.append(stack.pop())

        return output

    def eval_postfix(self, expression):
        stack = deque()
        for token in expression:
            if token == "f":
                stack.append(False)
            elif token == "t":
                stack.append(True)
            elif token == "1":
                stack.append(1)
            else:
                b = stack.pop()
                a = stack.pop()

                if token == "|":
                    stack.append(a or b)
                elif token == "&":
                    stack.append(a and b)
                elif token == "!":
                    stack.append(not b)  # a is set to 1 and is ignored here
                else:
                    raise Exception(f"Unsupported token: {token}")
        return stack.pop()
