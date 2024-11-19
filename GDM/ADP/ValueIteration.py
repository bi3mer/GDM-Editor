from typing import Dict

from ..utility import reset_utility, create_policy, calculate_max_utility
from ..Graph import Graph

def __in_place_value_iteration(G: Graph, max_iteration: int, gamma: float, theta: float):
    for k in range(max_iteration):
        delta = 0

        for n in G.nodes:
            node = G.get_node(n)
            u = calculate_max_utility(G, n, gamma)
            delta = max(delta, abs(node.utility - u))
            node.utility = u

        print(f'delta={delta}')
        if delta < theta:
            break
            
    print(f'{k} iterations to converge.')

def __value_iteration(G: Graph, max_iteration: int, gamma: float, theta: float):
    for _ in range(max_iteration):
        delta = 0
        u_temp: Dict[str, float] = {}

        for n in G.nodes:
            u = calculate_max_utility(G, n, gamma)
            delta = max(delta, abs(G.utility(n) - u))
            u_temp[n] = u
        
        G.set_node_utilities(u_temp)

        if delta < theta:
            break

def value_iteration(
        G: Graph, max_iteration: int, gamma: float, theta: float, 
        in_place: bool=False, should_reset_utility: bool=True) -> Dict[str, str]:
            
    if should_reset_utility:
        reset_utility(G)

    if in_place:
        __in_place_value_iteration(G, max_iteration, gamma, theta)
    else:
        __value_iteration(G, max_iteration, gamma, theta)

    return create_policy(G, gamma)

