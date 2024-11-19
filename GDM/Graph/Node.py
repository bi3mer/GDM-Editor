from dataclasses import dataclass
from typing import Set

@dataclass
class Node:
    name: str
    reward: float
    utility: float
    is_terminal: bool
    neighbors: Set[str]