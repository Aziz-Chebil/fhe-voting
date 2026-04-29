# fhe-voting


## Limitations

This is a demo of the FHE primitive — encrypted aggregation with key separation — not a production voting system. Several legitimacy properties a real system would need are deliberately out of scope, and a few are worth being explicit about.

**Voter authentication is stubbed.** The `/vote` endpoint accepts a voter ID via the `X-Voter-ID` header and rejects duplicates within a server lifetime. There is no signature, no enrollment, no proof that the submitter is who they claim to be. A real system would bind ballots to authenticated identities (e.g., signed credentials issued during voter registration). The dedup logic here prevents accidental double-submission and trivially-scripted ballot stuffing, nothing more.

**Ballot validation is structural, not cryptographic.** The server checks that incoming ciphertexts fall within an expected size range and successfully deserialize under the public context. This catches malformed uploads, truncated requests, and ciphertexts encrypted under a different context. It does *not* verify that a ballot encrypts a value in `{0, 1}` — the server cannot decrypt, and TenSEAL's protobuf-based deserializer is permissive enough that some adversarially crafted byte sequences parse as syntactically valid ciphertexts encrypting arbitrary plaintexts. A modified client could submit a ciphertext encrypting `999`, which would pass structural validation and corrupt the final tally.

Cryptographically enforcing valid plaintexts requires a zero-knowledge proof attached to each ballot, demonstrating that the ciphertext encrypts a value in the allowed set without revealing which one. Helios uses Chaum-Pedersen disjunctive proofs over ElGamal for exactly this purpose; lattice analogues for BFV exist in the literature but are not available in TenSEAL or any drop-in Python library. Implementing one is multi-week work and out of scope for a one-week demo.

**Trust in the authority is total.** A single authority holds the secret key and is trusted to (a) decrypt only the final tally, never individual ballots, and (b) report the result honestly. Threshold decryption — splitting the secret key among multiple authorities so no single party can decrypt alone — is the standard production answer and is not implemented here.

**State is in-memory.** Voter IDs, the running tally, and ballot count all live in the server process. Restarting the server resets the election. A real deployment would persist these and add proper synchronization for multi-worker setups.