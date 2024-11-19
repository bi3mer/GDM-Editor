from GDM.Graph import Graph

from random import choice
from typing import Dict


def random_policy(G: Graph) -> Dict[str, str]:
    pi: Dict[str, str] = {}
    for node in G.nodes.values():
        if not node.is_terminal:
            pi[node.name] = choice(list(node.neighbors))

    return pi