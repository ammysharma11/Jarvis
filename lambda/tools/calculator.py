"""Calculator tool"""
import re
import math
from tools.base import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Perform mathematical calculations. Use for any math questions."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate, e.g., '(25 * 4) + 10', 'sqrt(144)', '15% of 200'"
            }
        },
        "required": ["expression"]
    }
    
    # Safe functions for eval
    SAFE_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'pow': pow,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'pi': math.pi,
        'e': math.e
    }
    
    def execute(self, expression: str) -> ToolResult:
        """Evaluate math expression safely"""
        
        try:
            # Preprocess expression
            expr = expression.lower().strip()
            
            # Handle percentage calculations
            # "15% of 200" -> "(15/100) * 200"
            percent_match = re.match(r'(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)', expr)
            if percent_match:
                pct, num = percent_match.groups()
                expr = f"({pct}/100) * {num}"
            
            # Replace common words
            expr = expr.replace('x', '*').replace('×', '*').replace('÷', '/')
            expr = expr.replace('^', '**')
            expr = expr.replace('plus', '+').replace('minus', '-')
            expr = expr.replace('times', '*').replace('divided by', '/')
            
            # Validate - only allow safe characters
            if not re.match(r'^[\d\s\+\-\*\/\(\)\.\,\%\w]+$', expr):
                return ToolResult(
                    success=False,
                    error="Invalid characters in expression"
                )
            
            # Evaluate safely
            result = eval(expr, {"__builtins__": {}}, self.SAFE_FUNCTIONS)
            
            # Format result
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 4)
            
            return ToolResult(
                success=True,
                data={"expression": expression, "result": result},
                message=f"{expression} = {result}"
            )
            
        except ZeroDivisionError:
            return ToolResult(success=False, error="Cannot divide by zero")
        except Exception as e:
            return ToolResult(success=False, error=f"Calculation error: {str(e)}")
