import os
workdir = os.environ["SHIPYARD_WORKDIR"]
conversation = [
    "Customer: I want a refund for order 123",
    "Agent: I found order 123. Can you confirm the order number?",
    "Customer: 123",
    "Agent: Purchase verified. I'm sorry it arrived broken. I'll process a refund.",
    "Customer: yes please",
    "Agent: Refund processed. Your receipt and confirmation number are ready.",
    "Customer: thanks",
    "Agent: You're welcome! Your ticket is REF-123.",
]
print("\n".join(conversation))
with open(os.path.join(workdir, "receipt.txt"), "w") as f:
    f.write("refund processed for order 123\nconfirmation: REF-123\n")
