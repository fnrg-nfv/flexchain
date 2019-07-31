import copy

from pulp import *

from para_placement.model import *
# bfs
from para_placement.model import _generate_configurations_for_one_route, _dijkstra


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

                # vnf_index = len(new_placement) - 1
                # node_capacity = topo.nodes[route[server_pos_list[next_server_pos]]]['computing_resource']
                # usage = sfc.vnf_list[vnf_index].computing_resource
                # while vnf_index > 0 and new_placement[vnf_index] == new_placement[vnf_index - 1]:
                #     vnf_index -= 1
                #     usage += sfc.vnf_list[vnf_index].computing_resource
                # if usage <= node_capacity:
                queue.append(new_placement)

    configurations = [Configuration(sfc, route, placement, route_latency, "{}_{}".format(route_idx, idx)) for
                      idx, placement in enumerate(placement_set)]
    for configuration in configurations:
        for node in configuration.computing_resource:
            if configuration.computing_resource[node] > topo.nodes[node]['computing_resource']:
                configurations.remove(configuration)
                break

    return configurations


def _route_capacity(topo: nx.Graph, route: List):
    return sum(topo.nodes[node]['computing_resource'] for node in route)


def _bfs_route(topo: nx.Graph, s, d, sfc: SFC) -> (List, float):
    queue = [([s], 0)]
    passed_node = [s]
    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource'] > 0]
    if d in servers:
        servers.remove(d)

    while queue:
        route, latency = queue.pop(0)
        cur_node = route[-1]

        if cur_node == d:
            return route, latency
        else:
            adjacent_nodes = topo[cur_node]
            for adj_node in adjacent_nodes:
                if adj_node in passed_node or adj_node in servers:
                    continue
                if topo[cur_node][adj_node]['bandwidth'] <= sfc.throughput:
                    continue
                passed_node.append(adj_node)
                new_route = route[:]
                new_route.append(adj_node)
                queue.append((new_route, latency + adjacent_nodes[adj_node]['latency']))

    return [], sys.maxsize


# deprecated
def _generate_routes_by_permutation(topo: nx.Graph, server_permutation, sfc: SFC) -> (List, float):
    route = []
    latency = 0
    for s, d in pairwise(server_permutation):
        sub_route, sub_latency = _bfs_route(topo, s, d, sfc)
        if not sub_route:
            return [], sys.maxsize
        route.extend(sub_route[:-1])
        latency += sub_latency
    route.append(server_permutation[-1])
    return route, latency


# deprecated
def _generate_configurations_dc_by_server(topo: nx.Graph, sfc: SFC):
    """
    Generate Configurations:
    1. Permute servers
    2. Generate routes by the server permutation
    3. Generate configurations by the routes
    :param topo:
    :param sfc:
    :return:
    """
    configurations = []
    routes = []
    sfc_min_usage = min(vnf.computing_resource for vnf in sfc.vnf_list)
    sfc_max_usage = max(vnf.computing_resource for vnf in sfc.vnf_list)
    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource'] >= sfc_min_usage]
    servers.sort(key=lambda node: topo.nodes[node]['computing_resource'], reverse=True)
    top_servers = servers[:len(sfc.vnf_list)]
    if sum(topo.nodes[server]['computing_resource'] for server in top_servers) < sfc.computing_resources_sum:
        return routes
    if topo.nodes[top_servers[0]]['computing_resource'] < sfc_max_usage:
        return routes

    route_idx = 0
    print(":{} ".format(len(sfc.vnf_list)), end="")
    for i in range(1, len(sfc.vnf_list) + 1):
        print("-{}({}) ".format(i, len(configurations)), end="")
        for server_permutation in itertools.permutations(servers, i):
            server_permutation = list(server_permutation)

            if all(topo.nodes[node]['computing_resource'] < sfc_max_usage for node in server_permutation) or \
                    _route_capacity(topo, server_permutation) < sfc.computing_resources_sum:
                continue

            route, route_latency = _generate_routes_by_permutation(topo, [sfc.s, *server_permutation, sfc.d], sfc)
            route_configurations = _generate_configurations_for_one_route_dc(topo, route, route_latency, sfc, route_idx)
            configurations.extend(route_configurations)
            route_idx += 1

            if len(configurations) >= config.K:
                return configurations

    return configurations


route_limit = 15
search_limit = 256 * 1024
# search_limit = 128 * 1024


def _generate_configurations_dc_by_bfs(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    queue = [([sfc.s], 0)]
    sfc_len = len(sfc.vnf_list)
    sfc_min_usage = min(vnf.computing_resource for vnf in sfc.vnf_list)
    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource'] >= sfc_min_usage]

    servers.sort(key=lambda node: topo.nodes[node]['computing_resource'], reverse=True)
    if sum(topo.nodes[server]['computing_resource'] for server in servers[:sfc_len]) < sfc.computing_resources_sum:
        return []

    idx = 0
    configurations = []

    search = 0
    last_search = 1024

    while queue:
        route, latency = queue.pop(0)
        last_node = route[-1]

        search += 1
        if search >= last_search * 2:
            last_search = search
            print(" -> {}({},{})".format(last_search, len(route),
                                         sum(topo.nodes[node]['computing_resource'] > 0 for node in route)),
                  end="")

        if len(route) >= route_limit or search >= search_limit:
            print("\nFULL({})".format(len(route)))
            break

        if route[-1] == sfc.d and sum(topo.nodes[node]['computing_resource'] for node in route
                                      if topo.nodes[node][
                                             'computing_resource'] > sfc_min_usage) >= sfc.computing_resources_sum:
            # accept the route (get the dest & the capacity is enough)

            route_configurations = _generate_configurations_for_one_route_dc(topo, route, latency, sfc, idx)
            if not route_configurations:
                route_configurations = _generate_configurations_for_one_route(topo, route, latency, sfc, idx)
            configurations.extend(route_configurations)
            idx += 1

            if len(configurations) >= config.K:
                break
        else:
            # extend the route
            adjacent_nodes = topo[last_node]
            for node in adjacent_nodes:

                available = True
                for n in reversed(route):
                    if n == node:
                        available = False
                        break
                    if topo.nodes[n]['computing_resource'] > sfc_min_usage:
                        break
                if not available:
                    continue

                adj_latency = adjacent_nodes[node]['latency']

                if latency + adj_latency > sfc.latency:
                    continue

                new_route = route[:]
                new_route.append(node)
                queue.append((new_route, latency + adj_latency))

    return configurations


def _generate_configurations_one_machine(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    queue = [([sfc.s], 0)]
    idx = 0
    configurations = []
    search = 0
    last_search = 1024

    if all(topo.nodes[node]['computing_resource'] < sfc.computing_resources_sum for node in topo.nodes):
        return []

    while queue:
        route, latency = queue.pop(0)
        last_node = route[-1]

        search += 1
        if search >= last_search * 2:
            last_search = search
            print(" -> {}({})".format(last_search, len(route)), end="")

        if len(route) >= route_limit or search >= search_limit:
            print("\nFULL({})".format(len(route)))
            break

        if route[-1] == sfc.d:
            # accept the route (get the dest & the capacity is enough)
            for node_idx, node in enumerate(route):
                if topo.nodes[node]['computing_resource'] >= sfc.computing_resources_sum:
                    configurations.append(Configuration(sfc, route, [node_idx] * len(sfc.vnf_list), latency, idx))
                    idx += 1

            if len(configurations) >= config.K:
                break
        else:
            # extend the route
            adjacent_nodes = topo[last_node]
            for node in adjacent_nodes:

                available = True
                for n in reversed(route):
                    if n == node:
                        available = False
                        break
                    if topo.nodes[n]['computing_resource'] >= sfc.computing_resources_sum:
                        break
                if not available:
                    continue

                adj_latency = adjacent_nodes[node]['latency']

                if latency + adj_latency > sfc.latency:
                    continue

                new_route = route[:]
                new_route.append(node)
                queue.append((new_route, latency + adj_latency))  # latency here is not important

    return configurations


def generate_configurations_dc(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    if config.ONE_MACHINE:
        return _generate_configurations_one_machine(topo, sfc)
    if config.DC_CHOOSING_SERVER:
        return _generate_configurations_dc_by_server(topo, sfc)
    return _generate_configurations_dc_by_bfs(topo, sfc)


# dfs
def generate_configuration_greedy_dc_dfs(topo: nx.Graph, sfc: SFC, deep: int = 10) -> Configuration:
    s = sfc.s
    d = sfc.d
    if len(sfc.vnf_list) == 0:
        route, latency = _bfs_route_general(topo, s, d, sfc)
        return Configuration(sfc, route, [], latency, 0)

    sfc_min_usage = sfc.vnf_list[0].computing_resource
    if config.ONE_MACHINE:
        sfc_min_usage = sfc.computing_resources_sum
    servers = [node for node in topo.nodes if topo.nodes[node]['computing_resource'] >= sfc_min_usage]
    shortest_distances = _dijkstra(topo, s)
    servers.sort(key=lambda server1: (shortest_distances[server1], -topo.nodes[server1]['computing_resource']))

    if len(servers) > deep:
        servers = servers[:deep]

    for server in servers:
        route, latency = _bfs_route_general(topo, s, server, sfc)

        if route:
            # build sub topology and sub sfc
            # topo = copy.deepcopy(topo)
            sub_sfc = copy.deepcopy(sfc)
            sub_sfc.latency -= latency
            sub_sfc.s = server
            placed_res = 0
            place = []
            while sub_sfc.vnf_list and sub_sfc.vnf_list[0].computing_resource <= topo.nodes[server][
                'computing_resource']:
                res = sub_sfc.vnf_list[0].computing_resource
                placed_res += res
                topo.nodes[server]['computing_resource'] -= res
                place.append(len(route) - 1)
                sub_sfc.vnf_list.pop(0)
            for edge in pairwise(route):
                topo.edges.get(edge)['bandwidth'] -= sub_sfc.throughput

            sub_configuration = generate_configuration_greedy_dc_dfs(topo, sub_sfc, max(int(deep / 2), 1))

            # back
            for edge in pairwise(route):
                topo.edges.get(edge)['bandwidth'] += sub_sfc.throughput
            topo.nodes[server]['computing_resource'] += placed_res

            if sub_configuration:
                for i in range(len(sub_configuration.place)):
                    sub_configuration.place[i] += (len(route) - 1)
                place.extend(sub_configuration.place)
                route.extend(sub_configuration.route[1:])
                latency += sub_configuration.route_latency
                return Configuration(sfc, route, place, latency, 0)

    return None


def _bfs_route_general(topo: nx.Graph, s, d, sfc: SFC) -> (List, float):
    queue = [([s], 0)]
    passed_node = [s]

    while queue:
        route, latency = queue.pop(0)
        cur_node = route[-1]

        if cur_node == d:
            return route, latency
        else:
            adjacent_nodes = topo[cur_node]
            for adj_node in adjacent_nodes:
                if adj_node in passed_node:
                    continue
                if topo[cur_node][adj_node]['bandwidth'] <= sfc.throughput:
                    continue
                passed_node.append(adj_node)
                new_route = route[:]
                new_route.append(adj_node)
                queue.append((new_route, latency + adjacent_nodes[adj_node]['latency']))

    return [], sys.maxsize
