import copy

from pulp import *

from para_placement.model import *
import time


def _generate_configurations_for_one_route_dc(topo: nx.Graph, route: List[int], route_latency: int, sfc: SFC,
                                              route_idx: int) -> List[Configuration]:
    server_pos_list = [idx for idx, node in enumerate(
        route) if topo.nodes[node]['computing_resource'] > 0]
    m = len(sfc.vnf_list)
    n = len(server_pos_list)

    placement_set = []
    queue = [[0]]

    while queue:
        cur_placement = queue.pop(0)
        last_server_index = cur_placement[-1]
        if len(cur_placement) == m:
            if cur_placement[-1] == n - 1:
                placement_set.append([server_pos_list[i]
                                      for i in cur_placement])
        else:
            for next_server_pos in range(last_server_index, min(last_server_index + 2, n)):
                new_placement = cur_placement[:]
                new_placement.append(next_server_pos)
                queue.append(new_placement)

    configurations = [Configuration(sfc, route, placement, route_latency, "{}_{}".format(route_idx, idx)) for
                      idx, placement in enumerate(placement_set)]

    def computing_resource_check(c, topo):
        return all(c.computing_resource[node] <= topo.nodes[node]['computing_resource']for node in c.computing_resource)

    configurations = [
        c for c in configurations if computing_resource_check(c, topo) and c.get_latency() <= sfc.latency]

    return configurations


def _route_capacity(topo: nx.Graph, route: List):
    return sum(topo.nodes[node]['computing_resource'] for node in route)


def _bfs_route(topo: nx.Graph, s, d, sfc: SFC) -> (List, float):
    queue = [([s], 0)]
    passed_node = [s]
    servers = [node for node in topo.nodes if topo.nodes[node]
               ['computing_resource'] > 0]
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
                if topo[cur_node][adj_node]['bandwidth'] < sfc.throughput:
                    continue
                passed_node.append(adj_node)
                new_route = route[:]
                new_route.append(adj_node)
                queue.append(
                    (new_route, latency + adjacent_nodes[adj_node]['latency']))

    return [], sys.maxsize


def _generate_routes_for_permutation(topo: nx.Graph, server_permutation, sfc: SFC) -> (List, float):
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


def _generate_configurations_permutation(topo: nx.Graph, sfc: SFC):
    """
    Generate Configurations:
    1. Permute servers
    2. Generate routes by the server permutation
    3. Generate configurations by the routes
    """
    configurations = []
    sfc_min_usage = min(vnf.computing_resource for vnf in sfc.vnf_list)
    sfc_max_usage = max(vnf.computing_resource for vnf in sfc.vnf_list)
    servers = [node for node in topo.nodes if topo.nodes[node]
               ['computing_resource'] >= sfc_min_usage]
    servers.sort(
        key=lambda node: topo.nodes[node]['computing_resource'], reverse=True)
    top_ratio = sum(topo.nodes[server]['computing_resource'] for server in servers[:len(
        sfc.vnf_list)]) / sfc.computing_resources_sum
    if top_ratio < 1.0:
        return[]
    elif top_ratio < 1.5:
        c = generate_configuration_greedy_dfs(topo, sfc)
        if c:
            configurations.append(c)
        return configurations
    if topo.nodes[servers[0]]['computing_resource'] < sfc_max_usage:
        return []
    pa = ParaAnalyzer(sfc.vnf_list)
    if pa.opt_latency > sfc.latency:
        return []
    if not config.PARA and sum(vnf.latency for vnf in sfc.vnf_list) > sfc.latency:
        return []

    route_idx = 0
    start = time.time()
    for i in range(1, len(sfc.vnf_list) + 1):
        for server_permutation in itertools.permutations(servers, i):

            server_permutation = list(server_permutation)

            if all(topo.nodes[node]['computing_resource'] < sfc_max_usage for node in server_permutation) or \
                    _route_capacity(topo, server_permutation) < sfc.computing_resources_sum:
                continue

            route, route_latency = _generate_routes_for_permutation(
                topo, [sfc.s, *server_permutation, sfc.d], sfc)
            route_configurations = _generate_configurations_for_one_route_dc(
                topo, route, route_latency, sfc, route_idx)
            configurations.extend(route_configurations)
            route_idx += 1

            if len(configurations) >= config.K:
                return configurations

            # timeout
            if time.time() - start > time_limit:
                print("timeout", sfc, pa.opt_latency,
                      len(configurations), top_ratio)
                c = generate_configuration_greedy_dfs(topo, sfc)
                if c:
                    print('greedy gen ok')
                    configurations.append(c)
                return configurations

    return configurations


time_limit = 3
route_limit = 15
search_limit = 256 * 1024


def _generate_configurations_bfs(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    queue = [([sfc.s], 0)]
    route_idx = 0
    configurations = []
    sfc_max_usage = max(vnf.computing_resource for vnf in sfc.vnf_list)

    if all(topo.nodes[node]['computing_resource'] < sfc_max_usage for node in topo.nodes):
        return []
    pa = ParaAnalyzer(sfc.vnf_list)
    if pa.opt_latency > sfc.latency:
        return []

    start = time.time()
    while queue:
        route, route_latency = queue.pop(0)
        last_node = route[-1]

        if time.time() - start > time_limit:
            print("timeout", sfc, pa.opt_latency,
                  len(configurations), len(route))
            c = generate_configuration_greedy_dfs(topo, sfc)
            if c:
                print('greedy gen ok')
                configurations.append(c)
            break

        if route[-1] == sfc.d:
            # accept the route (get the dest & the capacity is enough)
            route_configurations = _generate_configurations_for_one_route_dc(
                topo, route, route_latency, sfc, route_idx)
            configurations.extend(route_configurations)
            route_idx += 1
            if len(configurations) >= config.K:
                break
        else:
            # extend the route
            adjacent_nodes = topo[last_node]
            for node in adjacent_nodes:
                latency = adjacent_nodes[node]['latency']
                queue.append(([*route, node], route_latency + latency))

    return configurations


def _generate_configurations_one_machine_permutation(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    configurations = []
    servers = [node for node in topo.nodes if topo.nodes[node]
               ['computing_resource'] >= sfc.computing_resources_sum]
    pa = ParaAnalyzer(sfc.vnf_list)
    if pa.opt_latency > sfc.latency:
        return []

    for idx, server in enumerate(servers):
        route, route_latency = _generate_routes_for_permutation(
            topo, [sfc.s, server, sfc.d], sfc)
        place = [route.index(server) for vnf in sfc.vnf_list]
        route_configuration = Configuration(
            sfc, route, place, route_latency, idx)
        configurations.append(route_configuration)
    return configurations


def _generate_configurations_one_machine_bfs(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
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
                    configurations.append(Configuration(
                        sfc, route, [node_idx] * len(sfc.vnf_list), latency, idx))
                    idx += 1

            if len(configurations) >= config.K:
                break
        else:
            # extend the route
            adjacent_nodes = topo[last_node]
            for node in adjacent_nodes:
                adj_latency = adjacent_nodes[node]['latency']

                if latency + adj_latency > sfc.latency:
                    continue

                new_route = route[:]
                new_route.append(node)
                # latency here is not important
                queue.append((new_route, latency + adj_latency))

    return configurations


def generate_configurations(topo: nx.Graph, sfc: SFC) -> List[Configuration]:
    if config.ONE_MACHINE:
        return _generate_configurations_one_machine_permutation(topo, sfc)
    if config.GC_BFS:
        return _generate_configurations_bfs(topo, sfc)
    return _generate_configurations_permutation(topo, sfc)


def generate_configuration_greedy_dfs(topo: nx.Graph, sfc: SFC, deep: int = 16) -> Configuration:
    s = sfc.s
    d = sfc.d
    if len(sfc.vnf_list) == 0:
        route, latency = _bfs_route_general(topo, s, d, sfc)
        return Configuration(sfc, route, [], latency, 0)

    sfc_min_requirement = sfc.vnf_list[0].computing_resource
    if config.ONE_MACHINE:
        sfc_min_requirement = sfc.computing_resources_sum
    servers = [node for node in topo.nodes if topo.nodes[node]
               ['computing_resource'] >= sfc_min_requirement]
    servers.sort(key=lambda s:  topo.nodes[s]
                 ['computing_resource'], reverse=True)

    if len(servers) > deep:
        servers = servers[:deep]

    for server in servers:
        route, latency = _bfs_route_general(topo, s, server, sfc)

        if route:
            # build sub topology and sub sfc
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

            sub_configuration = generate_configuration_greedy_dfs(
                topo, sub_sfc, max(int(deep / 2), 1))

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
                queue.append(
                    (new_route, latency + adjacent_nodes[adj_node]['latency']))

    return [], sys.maxsize
