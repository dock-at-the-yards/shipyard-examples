import os

def score(workdir):
    receipt = os.path.join(workdir, "receipt.txt")
    ok = os.path.exists(receipt) and "refund" in open(receipt).read().lower()
    return {"score": 1.0 if ok else 0.0, "passed": ok, "details": "receipt check"}
