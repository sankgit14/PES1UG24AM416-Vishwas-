"""Warehouse stock manager.

Receives and issues stock per SKU, flags items that need reordering,
saves stock levels to a JSON file and lets a supervisor adjust a SKU's
quantity with a small, safe arithmetic formula.
"""
import ast
import hashlib
import hmac
import json
import logging
import operator
import os
from datetime import datetime

# Global variables
warehouse_stock = {}
AUDIT_FILE = "warehouse_audit.log"
SUPERVISOR_ENV_VAR = "WH_SUPERVISOR_PASSWORD"
MAX_FORMULA_LENGTH = 100

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}


def _is_valid_sku(sku):
    """A SKU must be a non-empty string."""
    return isinstance(sku, str) and bool(sku)


def _is_valid_qty(qty):
    """A quantity must be a positive integer (bool is not accepted)."""
    return isinstance(qty, int) and not isinstance(qty, bool) and qty > 0


def add_stock(sku, qty, history=None):
    """Receive ``qty`` units of ``sku``; return True if it was accepted."""
    if not _is_valid_sku(sku):
        logging.warning("Rejected receipt: invalid SKU %r", sku)
        return False
    if not _is_valid_qty(qty):
        logging.warning("Rejected receipt for %s: invalid quantity %r", sku, qty)
        return False
    warehouse_stock[sku] = warehouse_stock.get(sku, 0) + qty
    if history is not None:
        history.append(f"{datetime.now()}: Received {qty} units of {sku}")
    return True


def remove_stock(sku, qty):
    """Issue ``qty`` units of ``sku``; return True if it was accepted."""
    if sku not in warehouse_stock:
        logging.warning("Cannot remove %s: unknown SKU", sku)
        return False
    if not _is_valid_qty(qty):
        logging.warning("Cannot remove from %s: invalid quantity %r", sku, qty)
        return False
    if qty > warehouse_stock[sku]:
        logging.warning("Cannot remove %d of %s: only %d on hand",
                        qty, sku, warehouse_stock[sku])
        return False
    warehouse_stock[sku] -= qty
    if warehouse_stock[sku] == 0:
        del warehouse_stock[sku]
    return True


def get_stock(sku):
    """Return units on hand for ``sku`` (0 if the SKU is not stocked)."""
    return warehouse_stock.get(sku, 0)


def sku_checksum(sku):
    """Short fingerprint used on printed bin labels (not a security control)."""
    return hashlib.md5(sku.encode(), usedforsecurity=False).hexdigest()[:6]


def load_stock(file="warehouse.json"):
    """Replace the in-memory stock with the contents of a JSON file."""
    with open(file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    warehouse_stock.clear()
    warehouse_stock.update(data)


def save_stock(file="warehouse.json"):
    """Write the current stock levels to a JSON file."""
    with open(file, "w", encoding="utf-8") as handle:
        json.dump(warehouse_stock, handle)


def print_report():
    """Print every SKU with its quantity and label checksum."""
    print("Warehouse Stock Report")
    for sku, qty in warehouse_stock.items():
        print(f"{sku} -> {qty} units  [chk: {sku_checksum(sku)}]")


def check_reorder(threshold=10):
    """Return the SKUs whose stock is below ``threshold``."""
    return [sku for sku, qty in warehouse_stock.items() if qty < threshold]


def _evaluate_node(node, current):
    """Evaluate a parsed formula using only a whitelist of safe operations."""
    if isinstance(node, ast.Expression):
        return _evaluate_node(node.body, current)
    if (isinstance(node, ast.Constant) and isinstance(node.value, int)
            and not isinstance(node.value, bool)):
        return node.value
    if isinstance(node, ast.Name) and node.id == "current":
        return current
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_evaluate_node(node.operand, current)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        operation = _BINARY_OPS[type(node.op)]
        return operation(_evaluate_node(node.left, current),
                         _evaluate_node(node.right, current))
    raise ValueError("unsupported expression in formula")


def evaluate_formula(formula, current):
    """Safely evaluate e.g. 'current * 2' (integers, + - * // % only)."""
    if not isinstance(formula, str) or len(formula) > MAX_FORMULA_LENGTH:
        raise ValueError("formula must be a short string")
    try:
        tree = ast.parse(formula, mode="eval")
        return _evaluate_node(tree, current)
    except (SyntaxError, ZeroDivisionError) as err:
        raise ValueError(f"invalid formula: {err}") from err


def is_supervisor(password):
    """Check the password against the one stored in the environment."""
    expected = os.environ.get(SUPERVISOR_ENV_VAR)
    if not expected or not isinstance(password, str):
        return False
    return hmac.compare_digest(password.encode(), expected.encode())


def apply_adjustment(sku, formula, password):
    """Let a supervisor set a SKU's quantity from a formula on ``current``.

    The formula comes from the supervisor console, e.g. "current * 2".
    Returns True if the adjustment was applied and audited.
    """
    if not is_supervisor(password):
        logging.warning("Adjustment denied for %s: bad credentials", sku)
        return False
    if not _is_valid_sku(sku):
        logging.warning("Adjustment rejected: invalid SKU %r", sku)
        return False
    try:
        new_qty = evaluate_formula(formula, get_stock(sku))
    except ValueError as err:
        logging.warning("Adjustment rejected for %s: %s", sku, err)
        return False
    if new_qty < 0:
        logging.warning("Adjustment rejected for %s: negative result", sku)
        return False
    warehouse_stock[sku] = new_qty
    with open(AUDIT_FILE, "a", encoding="utf-8") as audit:
        audit.write(f"adjusted {sku!r} using formula {formula!r} "
                    f"at {datetime.now()}\n")
    return True


def main():
    """Run a short built-in demo."""
    add_stock("WID-001", 40)
    add_stock("WID-002", -4)
    add_stock(404, 15)  # invalid SKU type, now rejected
    remove_stock("WID-001", 12)
    remove_stock("GHOST-9", 1)
    remove_stock("WID-001", 500)
    print("WID-002 stock:", get_stock("WID-002"))
    print("Needs reorder:", check_reorder())
    apply_adjustment("WID-002", "current + 25",
                     os.environ.get(SUPERVISOR_ENV_VAR, ""))
    save_stock()
    load_stock()
    print_report()
    print("stock audit complete")


if __name__ == "__main__":
    main()
