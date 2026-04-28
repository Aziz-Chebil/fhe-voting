# vote.py — simulates voters fetching the public context from the server
# and submitting encrypted ballots. Has no access to the secret key.
import requests
import tenseal as ts

SERVER = "http://127.0.0.1:8000"

# Step 1: fetch the public context the server is using.
# A real voter app would do exactly this on startup.
r = requests.get(f"{SERVER}/public-context")
r.raise_for_status()
public_context = ts.context_from(r.content)
assert not public_context.is_private(), "voter received a context with a secret key"
print(f"Fetched public context ({len(r.content):,} bytes). is_private={public_context.is_private()}")

# Step 2: cast 5 ballots. Expected tally: 3 yes, 2 no.
votes = [1, 0, 1, 1, 0]
for i, v in enumerate(votes):
    ballot = ts.bfv_vector(public_context, [v])
    payload = ballot.serialize()
    r = requests.post(f"{SERVER}/vote", data=payload,
                      headers={"Content-Type": "application/octet-stream"})
    r.raise_for_status()
    print(f"Voter {i} submitted (vote was {v}, but server can't see that): {r.json()}")

print("\nAll ballots submitted. Run decrypt_tally.py to see the result.")