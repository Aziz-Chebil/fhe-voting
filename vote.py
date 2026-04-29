# vote.py — simulates voters fetching the public context from the server
# and submitting encrypted ballots. Has no access to the secret key.
import requests
import tenseal as ts

SERVER = "http://127.0.0.1:8000"

def main():
    # Step 1: fetch the public context the server is using.
    r = requests.get(f"{SERVER}/public-context")
    r.raise_for_status()
    public_context = ts.context_from(r.content)
    assert not public_context.is_private(), "voter received a context with a secret key"
    print(f"Fetched public context ({len(r.content):,} bytes). is_private={public_context.is_private()}")

    # Step 2: cast 5 ballots. Expected tally: 3 yes, 2 no.
    votes = [1, 0, 1, 1, 0]
    for i, v in enumerate(votes):
        voter_id = f"voter-{i}"
        ballot = ts.bfv_vector(public_context, [v])
        payload = ballot.serialize()
        r = requests.post(
            f"{SERVER}/vote",
            data=payload,
            headers={
                "Content-Type": "application/octet-stream",
                "X-Voter-ID": voter_id,
            },
        )
        if r.status_code == 409:
            print(f"  voter-{i}: rejected (already voted)")
            continue
        r.raise_for_status()
        print(f"Voter {i} submitted (vote was {v}, but server can't see that): {r.json()}")

    print("\nAll ballots submitted. Run decrypt_tally.py to see the result.")

if __name__ == "__main__":
    main()