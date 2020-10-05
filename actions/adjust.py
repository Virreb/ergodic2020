from game_state import GameState
def heat(game_layer, temperature_threshold=3):
    state: GameState = game_layer.game_state

    return_dict = {'text': None, 'callback': None, 'args': None}

    if state.funds <= 150:
        return return_dict

    for b in state.residences:
        blueprint = game_layer.get_residence_blueprint(b.building_name)
        if state.temp_diff > 0:
            newTemp = 19.5
        elif state.temp_diff < 0:
            newTemp = 22.5
        else:
            newTemp = 21
        tmp_diff = b.temperature - newTemp
        if abs(tmp_diff) > temperature_threshold:
            indoorTemp = b.temperature
            outdoorTemp = state.current_temp
            emissivity = blueprint.emissivity
            currentPop = b.current_pop
            degreesPerPop = 0.04
            degreesPerExcessMwh = 0.75
            baseEnergyNeed = blueprint.base_energy_need
            effectiveEnergyIn = (newTemp - indoorTemp + (indoorTemp - outdoorTemp) * emissivity - degreesPerPop * currentPop)/degreesPerExcessMwh + baseEnergyNeed

            if b.effective_energy_in > blueprint.base_energy_need:
                effectiveEnergyIn = blueprint.base_energy_need
            elif effectiveEnergyIn < baseEnergyNeed:
                continue
            return_dict['text'] = f'Adjusted heat on: {b.building_name} with current temperature {b.temperature}'
            return_dict['callback'] = game_layer.adjust_energy_level
            return_dict['args'] = ((b.X, b.Y), effectiveEnergyIn)

    return return_dict
