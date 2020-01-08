from para_placement.model import Model


def evaluate(model: Model) -> bool:
    accepted_sfc_list = model.get_accepted_sfc_list()

    # latency constraints
    for sfc in accepted_sfc_list:
        if sfc.accepted_configuration.get_latency() > sfc.latency:
            return False

    # computing resource constraints
    for index, info in model.topo.nodes.data():
        usage = sum(sfc.accepted_configuration.computing_resource[index]
                    for sfc in accepted_sfc_list
                    if index in sfc.accepted_configuration.computing_resource)
        if usage > info['computing_resource']:
            return False

    # throughput constraints
    for start, end, info in model.topo.edges.data():
        usage = sum(sfc.throughput * sfc.accepted_configuration.edges[(start, end)]
                    for sfc in accepted_sfc_list
                    if (start, end) in sfc.accepted_configuration.edges)
        if usage > info['bandwidth']:
            return False

    return True


def objective_value(model: Model) -> float:
    return len(model.get_accepted_sfc_list())


def average_latency(model: Model) -> float:
    accepted_sfc_list = model.get_accepted_sfc_list()
    if len(accepted_sfc_list) == 0:
        return 0
    return sum(sfc.accepted_configuration.get_latency() for sfc in accepted_sfc_list) / len(accepted_sfc_list)
