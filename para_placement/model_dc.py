from pulp import *

from para_placement.config import K, DC_CHOOSING_SERVER
from para_placement.helper import pairwise
from para_placement.model import *
from para_placement.model import _generate_configurations_for_one_route


def _bfs_route(topo: nx.Graph, s, d) -> (List, float):
    if (s, d) in _bfs_route.cache:
        return _bfs_route.cache[(s, d)]

    queue = [([s], 0)]

    while queue:
        route, latency = queue.pop(0)

        if route[-1] == d:
            _bfs_route.cache[(s, d)] = (route, latency)
            return route, latency
        else:
            adjacent_nodes = topo[route[-1]]
            for adj_node in adjacent_nodes:
                if adj_node in route:
                    continue
                new_route = route[:]
                new_route.append(adj_node)
                queue.append((new_route, latency + adjacent_nodes[adj_node]['latency']))

    return [], sys.maxsize


_bfs_route.cache = {}


def _permutation_to_route(topo: nx.Graph, server_permutation) -> (List, float):
    route = []
    latency = 0
    for s, d in pairwise(server_permutation):
        sub_route, sub_latency = _bfs_route(topo, s, d)
        route.extend(sub_route[:-1])
        latency += sub_latency
    route.append(server_permutation[-1])
    return route, latency


def _generate_route_list_dc_by_server(topo: nx.Graph, sfc: SFC):
    routes = []
    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource'] > 0]

    for i in range(1, len(sfc.vnf_list)):
        for server_permutation in itertools.permutations(servers, i):
            server_permutation = list(server_permutation)
            if _route_capacity(topo, server_permutation) > sfc.vnf_computing_resources_sum:
                routes.append(_permutation_to_route(topo, [sfc.s, *server_permutation, sfc.d]))
                if len(routes) > K:
                    return routes

    return routes


def _route_capacity(topo: nx.Graph, route: List):
    return sum(topo.nodes[node]['computing_resource'] for node in route)


def _generate_route_list_dc(topo: nx.Graph, sfc: SFC):
    routes = []
    queue = [([sfc.s], 0, 0)]
    sfc_len = len(sfc.vnf_list)

    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource'] > 0]
    servers.sort(key=lambda node: topo.nodes[node]['computing_resource'], reverse=True)
    top_servers = servers[:sfc_len]
    if sum(topo.nodes[server]['computing_resource'] for server in top_servers) < sfc.vnf_computing_resources_sum:
        return routes

    route_server_size_max = 0

    while queue:
        route, latency, route_servers_size = queue.pop(0)

        # route_servers_size = sum(1 for node in route if topo.nodes[node]['computing_resource'] > 0)
        if topo.nodes[route[-1]]['computing_resource'] > 0:
            route_servers_size += 1
        if route_server_size_max < route_servers_size:
            route_server_size_max = route_servers_size
            print(" -> {}".format(route_servers_size), end="")

        if route_servers_size > sfc_len:
            continue

        if latency > sfc.latency:
            continue

        if route[-1] == sfc.d and _route_capacity(topo, route) >= sfc.vnf_computing_resources_sum:
            routes.append((route, latency))
            if len(routes) >= K:
                break
        else:
            adjacent_nodes = topo[route[-1]]
            for node in adjacent_nodes:

                available = True
                for n in reversed(route):
                    if n == node:
                        available = False
                        break
                    if topo.nodes[n]['computing_resource'] > 0:
                        break
                if not available:
                    continue

                new_route = route[:]
                new_route.append(node)
                queue.append((new_route, latency + adjacent_nodes[node]['latency'],
                              route_servers_size))  # latency here is not important

    return routes


def generate_configurations_dc(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    if DC_CHOOSING_SERVER:
        routes = _generate_route_list_dc_by_server(topo, sfc)
    else:
        routes = _generate_route_list_dc(topo, sfc)

    print(" ... Size of route_list: {}".format(len(routes)), end="")

    configurations = []
    for idx, item in enumerate(routes):
        route, route_latency = item
        configurations.extend(_generate_configurations_for_one_route(topo, route, route_latency, sfc, idx))

    return configurations
