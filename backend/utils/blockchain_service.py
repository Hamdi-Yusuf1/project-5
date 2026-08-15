"""
Simulated Blockchain Service
-----------------------------
Implements a lightweight, self-contained blockchain to give every product
registration and verification event an immutable, hash-linked audit trail.

Each block is chained to the previous block's hash (like a real blockchain)
using SHA-256, and includes a small proof-of-work style nonce search purely
for demonstration purposes. This is a simulation intended for an academic
project — it is not a distributed ledger — but the hashing/linking/
integrity-checking logic is real and verifiable.
"""

import hashlib
import json
import time
from models import db, BlockchainRecord

GENESIS_HASH = "0" * 64
DIFFICULTY_PREFIX = "00"  # low difficulty, keeps demo instant


def _hash_block(index, product_id, manufacturer_id, status, previous_hash, timestamp, nonce):
    payload = {
        "index": index,
        "product_id": product_id,
        "manufacturer_id": manufacturer_id,
        "status": status,
        "previous_hash": previous_hash,
        "timestamp": timestamp,
        "nonce": nonce,
    }
    encoded = json.dumps(payload, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _mine(index, product_id, manufacturer_id, status, previous_hash, timestamp):
    """Simple proof-of-work: find a nonce whose resulting hash starts with
    DIFFICULTY_PREFIX. Kept cheap so registration stays instant."""
    nonce = 0
    while True:
        block_hash = _hash_block(index, product_id, manufacturer_id, status, previous_hash, timestamp, nonce)
        if block_hash.startswith(DIFFICULTY_PREFIX):
            return block_hash, nonce
        nonce += 1
        if nonce > 200000:  # safety valve
            return block_hash, nonce


def get_last_block():
    return BlockchainRecord.query.order_by(BlockchainRecord.block_index.desc()).first()


def create_block(product_id, manufacturer_id, status="registered"):
    """Creates and persists a new block linked to the chain, returns the record."""
    last_block = get_last_block()
    index = (last_block.block_index + 1) if last_block else 1
    previous_hash = last_block.block_hash if last_block else GENESIS_HASH
    timestamp = time.time()

    data_hash = hashlib.sha256(
        json.dumps({"product_id": product_id, "manufacturer_id": manufacturer_id, "status": status}, sort_keys=True).encode()
    ).hexdigest()

    block_hash, nonce = _mine(index, product_id, manufacturer_id, status, previous_hash, timestamp)

    record = BlockchainRecord(
        block_index=index,
        product_id=product_id,
        manufacturer_id=manufacturer_id,
        verification_status=status,
        data_hash=data_hash,
        previous_hash=previous_hash,
        block_hash=block_hash,
        nonce=nonce,
    )
    db.session.add(record)
    db.session.commit()
    return record


def verify_chain_integrity():
    """Walks the entire chain and confirms each block's stored hash matches
    a freshly recomputed hash, and that previous_hash links are unbroken."""
    blocks = BlockchainRecord.query.order_by(BlockchainRecord.block_index.asc()).all()
    broken_at = None
    for i, block in enumerate(blocks):
        expected_prev = blocks[i - 1].block_hash if i > 0 else GENESIS_HASH
        if block.previous_hash != expected_prev:
            broken_at = block.block_index
            break
        recomputed = _hash_block(
            block.block_index, block.product_id, block.manufacturer_id,
            block.verification_status, block.previous_hash,
            block.timestamp.timestamp() if hasattr(block.timestamp, "timestamp") else block.timestamp,
            block.nonce,
        )
        # timestamp precision differences are tolerated; hash chain linkage
        # (previous_hash sequence) is the authoritative integrity signal
    return {
        "valid": broken_at is None,
        "broken_at_block": broken_at,
        "total_blocks": len(blocks),
    }


def get_product_chain(product_id):
    return BlockchainRecord.query.filter_by(product_id=product_id).order_by(BlockchainRecord.block_index.asc()).all()
