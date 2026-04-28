# setup.py — run once before starting the server.
# Generates the authority context (with secret key) and the public context
# (without secret key), and saves both to ./contexts/.
import os
import tenseal as ts

CONTEXT_DIR = "contexts"
os.makedirs(CONTEXT_DIR, exist_ok=True)

# Authority context: full context, holds the secret key.
authority_context = ts.context(
    scheme=ts.SCHEME_TYPE.BFV,
    poly_modulus_degree=4096,
    plain_modulus=1032193,
)
authority_context.generate_galois_keys()

auth_path = os.path.join(CONTEXT_DIR, "authority_context.bin")
with open(auth_path, "wb") as f:
    f.write(authority_context.serialize(save_secret_key=True))

# Public context: same crypto parameters, secret key stripped.
public_context = authority_context.copy()
public_context.make_context_public()

pub_path = os.path.join(CONTEXT_DIR, "public_context.bin")
with open(pub_path, "wb") as f:
    f.write(public_context.serialize())

# Sanity check: reload both from disk and confirm only the authority
# context can decrypt. This is the same security property as yesterday,
# but now over the file boundary.
with open(auth_path, "rb") as f:
    reloaded_auth = ts.context_from(f.read())
with open(pub_path, "rb") as f:
    reloaded_pub = ts.context_from(f.read())

assert reloaded_auth.is_private(), "authority context lost its secret key on disk"
assert not reloaded_pub.is_private(), "public context still has the secret key on disk"

print(f"Authority context: {auth_path}  ({os.path.getsize(auth_path):,} bytes)")
print(f"Public context:    {pub_path}  ({os.path.getsize(pub_path):,} bytes)")
print()
print("Keep authority_context.bin SECRET — it contains the decryption key.")
print("public_context.bin is what the server will serve to voters.")