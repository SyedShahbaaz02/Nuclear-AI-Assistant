# Copilot instructions

## General

- Keep answers short, precise, and informal.
- Always adhere to SOLID design principles.
- Avoid redundant comments; only include comments for complex or non-obvious code.
- 120 characters is the maximum line length. Ensure all generated code adheres to this limit.

## Python

- Follow PEP8 standards for code style and formatting.
- Use meaningful and descriptive names for variables, functions, and classes.
- Organize code into reusable modules and packages.
- Use Semantic Kernel for all AI code interactions

## Unit Testing

- Structure tests using Arrange, Act, Assert comments.
- Ensure tests are isolated and follow the Single Responsibility Principle.

## Design Principles

- Write modular, reusable, and maintainable code.
- Use dependency injection to decouple components.
- Favor composition over inheritance where applicable.

## Code Documentation
- Use docstrings for all public classes and methods.
- Keep documentation concise and focused on the purpose and usage of the code.
- Use type hints for function parameters and return types to improve code clarity.
- Ensure you use Google Style of formatting for example:

```python
def abc(a: int, c = [1,2]):
    """_summary_

    Args:
        a (int): _description_
        c (list, optional): _description_. Defaults to [1,2].

    Raises:
        AssertionError: _description_

    Returns:
        _type_: _description_
    """
    if a > 10:
        raise AssertionError("a is more than 10")

    return c
```
