import os

def score(workdir):
    receipt = os.path.join(workdir, "receipt.txt")
    if not os.path.exists(receipt):
        return {"score": 0.0, "passed": False, "details": "missing receipt"}
    text = open(receipt).read().lower()
    ok = "refund" in text and "confirmation" in text and "ref-123" in text
    return {"score": 1.0 if ok else 0.0, "passed": ok, "details": "receipt+confirmation check"}
