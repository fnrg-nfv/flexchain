import time

from pulp import *

from para_placement import topology
import para_placement.config as config
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
                if len(routes) >= config.K:
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
            if len(routes) >= config.K:
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
    if config.DC_CHOOSING_SERVER:
        return _generate_configurations_dc_by_server(topo, sfc)

    routes = _generate_route_list_dc(topo, sfc)

    print(" ... Size of route_list: {}".format(len(routes)), end="")

    configurations = []
    for idx, item in enumerate(routes):
        route, route_latency = item
        configurations.extend(_generate_configurations_for_one_route(topo, route, route_latency, sfc, idx))

    return configurations


def _generate_configurations_dc_by_server(topo: nx.Graph, sfc: SFC):
    configurations = []
    routes = []
    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource'] > 0]
    servers.sort(key=lambda node: topo.nodes[node]['computing_resource'], reverse=True)
    top_servers = servers[:len(sfc.vnf_list)]
    if sum(topo.nodes[server]['computing_resource'] for server in top_servers) < sfc.vnf_computing_resources_sum:
        return routes

    route_idx = 0
    for i in range(1, len(sfc.vnf_list) + 1):
        for server_permutation in itertools.permutations(servers, i):
            server_permutation = list(server_permutation)
            if _route_capacity(topo, server_permutation) > sfc.vnf_computing_resources_sum:
                route, latency = _permutation_to_route(topo, [sfc.s, *server_permutation, sfc.d])
                routes.append((route, latency))

                if len(routes) > 20:
                    for route, latency in routes:
                        route_configurations = _generate_configurations_for_one_route_dc(topo, route, latency, sfc,
                                                                                         route_idx)
                        configurations.extend(route_configurations)
                        route_idx += 1

                    if len(configurations) >= config.K:
                        return configurations
                    routes.clear()

    return configurations


# bfs
def _generate_configurations_for_one_route_dc(topo: nx.Graph, route: List[int], route_latency: int, sfc: SFC,
                                              route_idx: int) -> List[Configuration]:
    server_pos_list = [idx for idx, node in enumerate(route) if topo.nodes[node]['computing_resource'] > 0]
    m = len(sfc.vnf_list)
    n = len(server_pos_list)

    placement_set = []
    queue = [[0]]

    while queue:
        cur_placement = queue.pop(0)
        last_server_index = cur_placement[-1]
        if len(cur_placement) == m:
            if cur_placement[-1] == n - 1:
                placement_set.append([server_pos_list[i] for i in cur_placement])
        else:
            for next_server_pos in range(last_server_index, min(last_server_index + 2, n)):
                new_placement = cur_placement[:]
                new_placement.append(next_server_pos)

                vnf_index = len(new_placement) - 1
                node_capacity = topo.nodes[route[server_pos_list[next_server_pos]]]['computing_resource']
                usage = sfc.vnf_list[vnf_index].computing_resource
                while vnf_index > 0 and new_placement[vnf_index] == new_placement[vnf_index - 1]:
                    vnf_index -= 1
                    usage += sfc.vnf_list[vnf_index].computing_resource
                if usage <= node_capacity:
                    queue.append(new_placement)

    configuration_set = []
    for idx, placement in enumerate(placement_set):
        configuration = Configuration(sfc, route, placement, route_latency, "{}_{}".format(route_idx, idx))
        configuration_set.append(configuration)

    return configuration_set


def main():
    topo = topology.data_center_example()
    vnf_set = generate_vnf_set(size=30)
    sfc_size = 100
    model = Model(topo, generate_sfc_list2(topo, vnf_set, sfc_size))
    model.draw_topo(1)

    # Configuration.para = False
    # linear_programming(model)
    # rounding_to_integral(model, rounding_method=rounding_one)
    # model.clear()

    Configuration.para = True

    for sfc in model.sfc_list:
        print(len(sfc.vnf_list), sfc)
        t1 = time.time()
        sfc.configurations = _generate_configurations_dc_by_server(topo, sfc)
        t2 = time.time()
        print("outer time {}".format(t2 - t1))
        for configuration in sfc.configurations[-20:]:
            print(configuration)
        if t2 - t1 > 1:
            print("TIMEOUT !!!")


if __name__ == '__main__':
    main()
