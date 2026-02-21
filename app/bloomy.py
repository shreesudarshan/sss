import hashlib
import math
from typing import List
import base64
from typing import Optional

class BloomFilter:
    """
    Space-efficient probabilistic data structure for membership testing.
    False positives possible, no false negatives.
    """
    
    def __init__(self, size: int = 10000, hash_count: int = 7):
        """
        Initialize Bloom filter.
        
        size: number of bits in filter
        hash_count: number of hash functions
        """
        self.size = size
        self.hash_count = hash_count
        self.bit_array = bytearray((size + 7) // 8)
    
    def _hash(self, value: str, seed: int) -> int:
        """Generate hash with seed for multiple hash functions."""
        h = hashlib.sha256(f"{value}{seed}".encode()).digest()
        return int.from_bytes(h, 'big') % self.size
    
    def add(self, value: str) -> None:
        """Add value to Bloom filter."""
        for i in range(self.hash_count):
            index = self._hash(value, i)
            self.bit_array[index // 8] |= 1 << (index % 8)
    
    def check(self, value: str) -> bool:
        """Check if value might be in Bloom filter."""
        for i in range(self.hash_count):
            index = self._hash(value, i)
            if not (self.bit_array[index // 8] & (1 << (index % 8))):
                return False
        return True
    
    def serialize(self) -> str:
        """Serialize Bloom filter to base64."""
        return base64.b64encode(self.bit_array).decode()
    
    @classmethod
    def deserialize(cls, data: str) -> 'BloomFilter':
        """Deserialize Bloom filter from base64."""
        bit_array = base64.b64decode(data.encode())
        bf = cls()
        bf.bit_array = bytearray(bit_array)
        bf.size = len(bit_array) * 8
        return bf
