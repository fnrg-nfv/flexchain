from para_placement.model import Model


def evaluate(model: Model) -> bool:
    accepted_sfc_list = list(filter(lambda s: s.accepted_configuration is not None, model.sfc_list))
    # print("Evaluating... Accepted sfc: {}".format(len(accepted_sfc_list)))

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
        usage = sum(sfc.throughput
                    for sfc in accepted_sfc_list
                    if "{}:{}".format(start, end) in sfc.accepted_configuration.edges)
        if usage > info['bandwidth']:
            return False

    return True


def objective_value(model: Model, epsilon) -> float:
    objective = 0
    accepted_sfc_list = list(filter(lambda s: s.accepted_configuration is not None, model.sfc_list))
    objective += len(accepted_sfc_list)

    for sfc in accepted_sfc_list:
        objective -= sfc.accepted_configuration.get_latency() * epsilon

    return objective
