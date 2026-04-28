# decrypt_tally.py — the authority. Loads the secret-key-bearing context
# from local disk, fetches the encrypted tally over HTTP, and decrypts it.
# This is the only place in the entire system that can produce a plaintext.
import requests
import tenseal as ts

SERVER = "http://127.0.0.1:8000"

# Step 1: load the authority context (contains the secret key).
# This file lives only on the authority's machine — not on the server.
with open("contexts/authority_context.bin", "rb") as f:
    authority_context = ts.context_from(f.read())
assert authority_context.is_private(), "authority context is missing its secret key"

# Step 2: fetch the encrypted tally from the server.
r = requests.get(f"{SERVER}/tally")
r.raise_for_status()
tally_bytes = r.content
print(f"Fetched encrypted tally ({len(tally_bytes):,} bytes) from server.")

# Step 3: deserialize under the authority context (which has the secret key)
# and decrypt. This is the moment the system produces a plaintext result.
tally = ts.bfv_vector_from(authority_context, tally_bytes)
result = tally.decrypt()
print(f"\nDecrypted tally: {result[0]} yes votes")