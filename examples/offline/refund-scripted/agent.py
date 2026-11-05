import os
workdir = os.environ["SHIPYARD_WORKDIR"]
conversation = [
    "Customer: I want a refund for order 123",
    "Agent: I found order 123. Can you confirm the order number?",
    "Customer: 123",
    "Agent: Refund processed. Your receipt is ready.",
    "Customer: thanks",
    "Agent: You're welcome!",
]
print("\n".join(conversation))
with open(os.path.join(workdir, "receipt.txt"), "w") as f:
    f.write("refund processed for order 123\n")
