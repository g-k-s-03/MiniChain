import time
import hashlib
from typing import List, Optional
from .transaction import Transaction
from .receipt import Receipt
from .serialization import canonical_json_hash

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _calculate_merkle_tree(hashes: List[str]) -> Optional[str]:
    if not hashes:
        return None
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        new_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            new_level.append(_sha256(combined))
        hashes = new_level
    return hashes[0]

def _calculate_merkle_root(transactions: List[Transaction]) -> Optional[str]:
    if not transactions:
        return None
    return _calculate_merkle_tree([tx.tx_id for tx in transactions])

def _calculate_receipt_root(receipts: List[Receipt]) -> Optional[str]:
    if not receipts:
        return None
    return _calculate_merkle_tree([canonical_json_hash(r.to_dict()) for r in receipts])

    # Logic moved to _calculate_merkle_tree


class Block:
    def __init__(
        self,
        index: int,
        previous_hash: str,
        transactions: Optional[List[Transaction]] = None,
        timestamp: Optional[float] = None,
        difficulty: Optional[int] = None,
        state_root: Optional[str] = None,
        receipt_root: Optional[str] = None,
        receipts: Optional[List[Receipt]] = None,
        miner: Optional[str] = None,
    ):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions: List[Transaction] = transactions or []
        self.receipts: List[Receipt] = receipts or []

        # Deterministic timestamp (ms)
        self.timestamp: int = (
            round(time.time() * 1000)
            if timestamp is None
            else int(timestamp)
        )

        self.difficulty: Optional[int] = difficulty
        self.nonce: int = 0
        self.hash: Optional[str] = None
        self.state_root: Optional[str] = state_root
        self.receipt_root: Optional[str] = receipt_root
        self.miner: Optional[str] = miner

        # NEW: compute merkle roots once
        self.merkle_root: Optional[str] = _calculate_merkle_root(self.transactions)
        
        # If receipt_root is missing but we have receipts, calculate it.
        if self.receipt_root is None and self.receipts:
            self.receipt_root = _calculate_receipt_root(self.receipts)

    # -------------------------
    # HEADER (used for mining)
    # -------------------------
    def to_header_dict(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "state_root": self.state_root,
            "receipt_root": self.receipt_root,
            "timestamp": self.timestamp,
            "difficulty": self.difficulty,
            "nonce": self.nonce,
            "miner": self.miner,
        }

    # -------------------------
    # BODY (transactions only)
    # -------------------------
    def to_body_dict(self):
        return {
            "transactions": [
                tx.to_dict() for tx in self.transactions
            ],
            "receipts": [
                r.to_dict() for r in self.receipts
            ]
        }

    # -------------------------
    # FULL BLOCK
    # -------------------------
    def to_dict(self):
        return {
            **self.to_header_dict(),
            **self.to_body_dict(),
            "hash": self.hash,
        }

    # -------------------------
    # HASH CALCULATION
    # -------------------------
    def compute_hash(self) -> str:
        return canonical_json_hash(self.to_header_dict())

    @classmethod
    def from_dict(cls, payload: dict):
        transactions = [
            Transaction.from_dict(tx_payload)
            for tx_payload in payload.get("transactions", [])
        ]
        receipts = [
            Receipt.from_dict(r_payload)
            for r_payload in payload.get("receipts", [])
        ]
        block = cls(
            index=payload["index"],
            previous_hash=payload["previous_hash"],
            transactions=transactions,
            timestamp=payload.get("timestamp"),
            difficulty=payload.get("difficulty"),
            state_root=payload.get("state_root"),
            receipt_root=payload.get("receipt_root"),
            receipts=receipts,
            miner=payload.get("miner"),
        )
        block.nonce = payload.get("nonce", 0)
        block.hash = payload.get("hash")
        if "merkle_root" in payload:
            block.merkle_root = payload["merkle_root"]
        return block
