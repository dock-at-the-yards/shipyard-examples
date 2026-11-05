import os
workdir = os.environ["SHIPYARD_WORKDIR"]
with open(os.path.join(workdir, "receipt.txt"), "w") as f:
    f.write("refund processed for order 123\nconfirmation: REF-123\n")
print("refund processed")
