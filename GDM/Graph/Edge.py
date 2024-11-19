from dataclasses import dataclass
from typing import Tuple, List

@dataclass
class Edge:
    src: str
    tgt: str
    probability: List[Tuple[str, float]]