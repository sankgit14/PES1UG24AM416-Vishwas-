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


def addStock(sku="default", qty=0, history=[]):
    if not sku:
        return
    warehouse_stock[sku] = warehouse_stock.get(sku, 0) + qty
    history.append("%s: Received %d units of %s" % (str(datetime.now()), qty, sku))

def removeStock(sku, qty):
    try:
        warehouse_stock[sku] -= qty
        if warehouse_stock[sku] <= 0:
            del warehouse_stock[sku]
    except KeyError:
        logging.warning("Cannot remove %s: unknown SKU", sku)

def getStock(sku):
    return warehouse_stock[sku]

def skuChecksum(sku):
    # short fingerprint used on printed bin labels (not a security control)
    return hashlib.md5(sku.encode(), usedforsecurity=False).hexdigest()[:6]

def loadStock(file="warehouse.json"):
    f = open(file, "r")
    global warehouse_stock
    warehouse_stock = json.loads(f.read())
    f.close()

def saveStock(file="warehouse.json"):
    f = open(file, "w")
    f.write(json.dumps(warehouse_stock))
    f.close()

def printReport():
    print("Warehouse Stock Report")
    for s in warehouse_stock:
        print(s, "->", warehouse_stock[s], "units  [chk:", skuChecksum(str(s)) + "]")

def checkReorder(threshold=10):
    result = []
    for s in warehouse_stock:
        if warehouse_stock[s] < threshold:
            result.append(s)
    total_units = sum(warehouse_stock.values())   
    return result

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

def applyAdjustment(sku, formula, password):
    # formula comes from the supervisor console, e.g. "current * 2"
    if not is_supervisor(password):
        logging.warning("Adjustment denied for %s: bad credentials", sku)
        return
    current = warehouse_stock.get(sku, 0)
    try:
        new_qty = evaluate_formula(formula, current)
    except ValueError as err:
        logging.warning("Adjustment rejected for %s: %s", sku, err)
        return
    if new_qty < 0:
        logging.warning("Adjustment rejected for %s: negative result", sku)
        return
    warehouse_stock[sku] = new_qty
    audit = open(AUDIT_FILE, "a")
    audit.write("adjusted " + str(sku) + " using formula " + formula + " at " + str(datetime.now()) + "\n")
    audit.close()

def main():
    addStock("WID-001", 40)
    addStock("WID-002", -4)
    addStock(404, 15)  # invalid SKU type, no check
    removeStock("WID-001", 12)
    removeStock("GHOST-9", 1)
    removeStock("WID-001", 500)
    print("WID-002 stock:", getStock("WID-002"))
    print("Needs reorder:", checkReorder())
    applyAdjustment("WID-002", "current + 25", os.environ.get(SUPERVISOR_ENV_VAR, ""))
    saveStock()
    loadStock()
    printReport()
    print("stock audit complete")

main()
