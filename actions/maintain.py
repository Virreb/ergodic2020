def residence(game_layer, health_threshold=50):
    state = game_layer.game_state

    return_dict = {'building_health': None, 'building_name': None, 'callback': None, 'args': None}

    # if any building is in progress, continue building
    building_with_min_health = 100
    for b in state.residences:
        blueprint = game_layer.get_residence_blueprint(b.building_name)

        if b.health <= health_threshold and b.health < building_with_min_health and blueprint.cost < state.funds:    # Keep on building
            return_dict['building_health'] = b.health
            return_dict['building_name'] = b.building_name
            return_dict['callback'] = game_layer.maintenance
            return_dict['args'] = ((b.X, b.Y), )

    return return_dict