from GDM.Graph import Graph

from typing import Dict
from math import inf

def greed_policy(G: Graph) -> Dict[str, str]:
    pi: Dict[str, str] = {}
    for node in G.nodes.values():
        if node.is_terminal:
            continue

        best_neighbor = None
        best_reward = -inf

        for neighbor_name in node.neighbors:
            r = G.reward(neighbor_name)
            if r > best_reward:
                best_reward = r
                best_neighbor = neighbor_name

        pi[node.name] = best_neighbor

    return pi