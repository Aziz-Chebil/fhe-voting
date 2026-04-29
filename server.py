# server.py — accepts encrypted ballots over HTTP, sums them without
# ever holding the secret key, exposes the encrypted tally for the
# authority to fetch and decrypt elsewhere.
from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional
from fastapi.responses import Response
import tenseal as ts

app = FastAPI(title="FHE Voting Server")

# Load the public context once at startup. Note: the server NEVER
# touches authority_context.bin. If this file existed on the server,
# the demo's security claim would be a lie.
PUBLIC_CONTEXT_PATH = "contexts/public_context.bin"
with open(PUBLIC_CONTEXT_PATH, "rb") as f:
    PUBLIC_CONTEXT_BYTES = f.read()
public_context = ts.context_from(PUBLIC_CONTEXT_BYTES)

# In-memory state. Restarting the server wipes the tally — that's
# fine for now; persistence is a later concern.
tally = None
ballot_count = 0


@app.get("/public-context")
def get_public_context():
    """Voters call this to fetch the public context they encrypt under."""
    return Response(content=PUBLIC_CONTEXT_BYTES, media_type="application/octet-stream")

_seen_voters: set[str] = set()
MIN_CT_BYTES = 1024
MAX_CT_BYTES = 1_000_000

@app.post("/vote")
async def vote(
    request: Request,
    x_voter_id: Optional[str] = Header(default=None, alias="X-Voter-ID"),
):
    """Accept one serialized BFV ciphertext, add it to the running tally."""
    if not x_voter_id:
        raise HTTPException(status_code=400, detail="missing X-Voter-ID header")

    if x_voter_id in _seen_voters:
        raise HTTPException(status_code=409, detail="voter_id already submitted")

    body = await request.body()
    global tally, ballot_count

    # Structural validation: size sanity.
    if not (MIN_CT_BYTES <= len(body) <= MAX_CT_BYTES):
        raise HTTPException(
            status_code=400,
            detail=f"ciphertext size {len(body)} outside expected range",
        )

    # Structural validation: deserialization under our public context.
    # This implicitly verifies the ciphertext's encoded parameters match ours.
    try:
        ballot = ts.bfv_vector_from(public_context, body)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid ciphertext")

    if tally is None:
        tally = ballot
    else:
        tally = tally + ballot
    ballot_count += 1
    _seen_voters.add(x_voter_id)  # only after successful tally update
    return {"status": "ok"}


@app.get("/tally")
def get_tally():
    """Return the encrypted tally. Anyone may fetch this; only the
    authority (which holds the secret key) can decrypt it."""
    if tally is None:
        raise HTTPException(status_code=404, detail="no votes submitted yet")
    return Response(content=tally.serialize(), media_type="application/octet-stream")


@app.get("/status")
def status():
    """Cheap liveness/sanity endpoint."""
    return {"ballots_received": ballot_count}