# Issue Table — `warehouse_stock_manager.py`

Line numbers refer to the **original** file. Severity is as reported by the tool (Bandit: High/Medium/Low; Pylint/Flake8 do not rank, so they are marked by category). Rows marked **(no tool)** are bugs I found by reading the program output, which none of the three tools reported.

| Issue | Type | Line(s) | Description | Fix Approach |
| ----- | ---- | ------- | ----------- | ------------ |
| Weak MD5 hash | Security — Bandit B324, **High** | 31 | `hashlib.md5` flagged as a weak hash for security use. Here it only makes a short fingerprint for printed bin labels. | `hashlib.md5(..., usedforsecurity=False)`: states the intent and keeps every printed label identical (switching to SHA-256 would have changed all labels). |
| `eval()` on supervisor formula | Security — Bandit B307 / Pylint W0123, **Medium** | 62 | `eval(formula, {"current": ...})` still exposes builtins, so input like `__import__('os').system(...)` runs arbitrary code. | Replaced with an AST whitelist evaluator (`evaluate_formula`): integers, the name `current`, unary minus and `+ - * // %` only. Anything else raises `ValueError`; length is capped at 100 chars; `/ 0` handled. |
| Pointless `eval()` on a constant | Security — Bandit B307 / Pylint W0123, **Medium** | 80 | `eval("print('stock audit complete')")` has no reason to be `eval`. | Replaced by a plain `print(...)`. |
| Hard-coded supervisor password | Security — Bandit B105, **Low** | 10, 59, 76 | Password in source (and repeated in the demo call), compared with `!=`. | Read from env var `WH_SUPERVISOR_PASSWORD`, compare with `hmac.compare_digest`, deny if the variable is unset (fail closed). Demo reads the env var instead of a literal. |
| Bare `except` + `pass` | Security/Quality — Bandit B110 **Low**, Pylint W0702, Flake8 E722 | 19-24 | Swallows every error silently, e.g. removing an unknown SKU just disappears. | Explicit checks (`sku not in warehouse_stock`, valid qty, enough stock) with `logging.warning(...)` and a boolean return. |
| Mutable default argument | Bug — Pylint W0102 | 12 | `history=[]` is created once and shared by every call, so entries leak between callers. | Default `None`; append only when a list is passed. |
| Negative / zero quantity accepted **(no tool)** | Bug | 15, 69 | `addStock("WID-002", -4)` stores **-4** units; the demo prints `WID-002 stock: -4` and flags it for reorder. | `_is_valid_qty`: positive `int` only (bool rejected); invalid receipts are logged and refused. |
| Over-removal deletes the SKU **(no tool)** | Bug | 20-22, 73 | `removeStock("WID-001", 500)` on 28 units drives it negative, then `<= 0` deletes the SKU, wiping stock with no error. | Reject when `qty > on_hand`; delete only when stock reaches exactly 0. |
| Invalid SKU type accepted **(no tool)** | Bug | 13, 70 | Only `if not sku` is checked, so `404` (int) is accepted. After a save/load round trip JSON turns the key into `"404"`; `str(s)` in the report hid the mismatch. | `_is_valid_sku`: non-empty `str` only. Removed the `str(s)` workaround. |
| `getStock` crashes on unknown SKU **(no tool)** | Bug | 27 | `warehouse_stock[sku]` raises `KeyError`. | `warehouse_stock.get(sku, 0)`. |
| `open()` without `with` / encoding | Quality — Pylint W1514, R1732 | 34, 40, 63 | Files not closed if an exception happens in between; platform-dependent encoding. | `with open(..., encoding="utf-8")`; `json.load` / `json.dump`. |
| `global` statement | Quality — Pylint W0603 | 35 | `loadStock` rebinds a module global. | `warehouse_stock.clear()` then `.update(data)` (mutate in place). |
| camelCase function names | Style — Pylint C0103 (x9) | 12, 18, 26, 29, 33, 39, 44, 49, 57 | Not PEP 8 snake_case. | Renamed: `add_stock`, `remove_stock`, `get_stock`, `sku_checksum`, `load_stock`, `save_stock`, `print_report`, `check_reorder`, `apply_adjustment`. |
| Missing docstrings | Style — Pylint C0114, C0116 | 1, 12-67 | No module or function documentation. | Added a module docstring and one for every function. |
| Unused imports | Quality — Pylint W0611, Flake8 F401 | 2, 4 | `logging` and `os` imported but unused. | Both are now used (logging for warnings, `os` for the env var). |
| Unused variable | Quality — Pylint W0612, Flake8 F841 | 54 | `total_units` computed and never used. | Removed; function is now a list comprehension. |
| Old-style string formatting | Style — Pylint C0209 | 16, 47 | `%` formatting and string concatenation. | f-strings. |
| Trailing whitespace | Style — Flake8 W291, Pylint C0303 | 54 | Spaces at end of line. | Removed. |
| Lines too long | Style — Flake8 E501 (x3), Pylint C0301 | 16, 47, 64 | Over 79 characters (line 64 is 107). | Re-wrapped; shorter docstring on `sku_checksum`. |
| Missing blank lines | Style — Flake8 E302 (x11), E305 | 12 ... 82 | Need 2 blank lines around top-level definitions. | Fixed. |
| `main()` runs on import | Quality | 82 | Importing the module runs the demo. | `if __name__ == "__main__": main()`. |

## Results

| Tool | Before | After |
| ---- | ------ | ----- |
| Bandit | 5 issues (1 High, 2 Medium, 2 Low) | 0 |
| Pylint | 4.48 / 10 | 10.00 / 10 |
| Flake8 | 19 findings | 0 |

Demo output before: `WID-002 stock: -4`, `Needs reorder: ['WID-002']`, report lists `404` (int SKU).
Demo output after (with `WH_SUPERVISOR_PASSWORD` set): invalid receipts and removals are logged and refused, `WID-002 stock: 0`, final report shows `WID-001 -> 28` and `WID-002 -> 25`.
