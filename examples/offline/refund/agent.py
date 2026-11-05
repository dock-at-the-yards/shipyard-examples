import os, sys
workdir = os.environ["SHIPYARD_WORKDIR"]
with open(os.path.join(workdir, "receipt.txt"), "w") as f:
    f.write("refund processed for order 123\n")
print("refund processed for order 123")
