def heat(game_layer, temperature_threshold=1.5):
    state = game_layer.game_state

    return_dict = {'text': None, 'callback': None, 'args': None}

    # if any building is in progress, continue building
    min_thres = 1.5
    for b in state.residences:
        blueprint = game_layer.get_residence_blueprint(b.building_name)
        newTemp = 21
        tmp_diff = b.temperature - newTemp
        if abs(tmp_diff) > min_thres:
            indoorTemp = b.temperature
            outdoorTemp = state.current_temp
            emissivity = blueprint.emissivity
            currentPop = b.current_pop
            degreesPerPop = 0.4
            degreesPerExcessMwh = 0.75
            baseEnergyNeed = blueprint.base_energy_need
            effectiveEnergyIn = (newTemp - indoorTemp + (indoorTemp - outdoorTemp) * emissivity - degreesPerPop * currentPop)/degreesPerExcessMwh + baseEnergyNeed

            return_dict['text'] = f'Adjusted heat on: {b.building_name} with current temperature {b.temperature}'
            return_dict['callback'] = game_layer.adjust_energy_level
            return_dict['args'] = ((b.X, b.Y), effectiveEnergyIn)
            min_thres = abs(tmp_diff)

    return return_dict
