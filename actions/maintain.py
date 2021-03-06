def residence(game_layer, health_threshold=70):
    state = game_layer.game_state

    return_dict = {'text': None, 'callback': None, 'args': None}

    # if any building is in progress, continue building
    building_with_min_health = 100
    for b in state.residences:
        blueprint = game_layer.get_residence_blueprint(b.building_name)
        # TODO: Also include nbr pop
        if b.health <= health_threshold and b.health < building_with_min_health and blueprint.cost < state.funds:
            return_dict['text'] = f'Maintained: {b.building_name} with health {b.health}'
            return_dict['callback'] = game_layer.maintenance
            return_dict['args'] = ((b.X, b.Y), )

    return return_dict
