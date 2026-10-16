# Reflection

## 1. Which issues were the easiest and which were the hardest to fix?

The easiest ones were the style and quality warnings: blank lines, long lines, trailing spaces, function names, missing docstrings, and the unused imports and variable. Most of these were quick edits.

The hardest was the eval() in apply_adjustment. The supervisor needs to type formulas like "current * 2", so I could not just delete it. I wrote a small parser that only allows whole numbers, the word "current" and the operators + - * // %, and rejects everything else. I tested it with a malicious formula, a divide by zero and a negative result, and all of them were refused.

The other hard part was the bugs that no tool reported. The original program stored -4 units for WID-002, removing 500 units wiped a SKU out completely, and the integer SKU 404 was accepted. I only found these by running the program and reading the output, and then I had to decide what the correct behaviour should be.

## 2. Did the tools report any false positives, or issues you chose to handle differently?

Yes, two. Bandit flagged MD5 (B324) as a weak hash. In this program MD5 is only used to make a short fingerprint for printed bin labels and has nothing to do with security. Switching to SHA-256 would have changed every printed label, so I kept MD5 and added usedforsecurity=False, which says the intent clearly and makes Bandit accept it.

Bandit also flagged my new constant PASSWORD_ENV_VAR as a hard-coded password (B105), only because its name contains "PASSWORD". The value is just the name of an environment variable, not a secret. I renamed the constant to SUPERVISOR_ENV_VAR instead of hiding the warning.

## 3. How would you integrate static analysis into your regular workflow?

I would run Flake8 and Pylint in my editor or in a pre-commit hook, so style and quality problems are caught while I write the code. I would run Bandit and Pylint in CI on every pull request, and block the merge if Bandit finds a Medium or High issue or the Pylint score drops below a minimum such as 9.5. If I ever need to ignore a warning, I would add a comment that explains why.

## 4. How did static analysis contribute to code quality, and what did it not catch?

The results were: Pylint 4.48/10 to 10.00/10, Bandit 5 issues to 0, and Flake8 19 findings to 0. The code is safer (no eval, no hard-coded password, no silent except/pass), easier to read (PEP 8 names and docstrings) and easier to maintain (no global statement and no shared mutable default argument).

However, a perfect score does not mean the program is correct. None of the tools noticed the negative stock, the over-removal bug or the integer SKU. Static analysis is a useful first check, but it has to be combined with running the program, testing and code review.