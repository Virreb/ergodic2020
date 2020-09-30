

def residence(game_layer, state):

    min_health = 100
    res_to_maintain = None
    for res in state.residences:

        if res.health < min_health:
            min_health = res.health
            res_to_maintain = res

    if res_to_maintain is not None:
        game_layer.maintenance((res_to_maintain.X, res_to_maintain.Y))
        return True
    else:
        return False

    # TODO: Return which building was maintained?

