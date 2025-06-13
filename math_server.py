# math_server.py

from fastmcp import FastMCP
mcp = FastMCP("Math Server", port=3334)
@mcp.tool(
    name="add_numbers",
    description="Складывает два числа"
    )
def add_numbers(a: float, b: float) -> float:
    """
    Складывает два числа.
    
    Args:
        a (number): Число, e.g., 3
        b (number): Число, e.g., 4
    
    Returns:
        number: Сумма числа 2 и 3
    """
    return a + b

if __name__ == "__main__":
    print("Запуск Math Server на порту 3334")
    mcp.run(transport="streamable-http")