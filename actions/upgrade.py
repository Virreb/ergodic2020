
def do(game_layer):
    state = game_layer.game_state

    # actions_dict = {'text': None, 'callback': None, 'args': None}

    actions_dict = {}
    for upgrade in state.available_upgrades:
        upgrade_type = upgrade.name

        if upgrade.cost < state.funds:

            building_max_pop = 0
            max_energy_need = -5
            max_temp_overflow = -5
            max_emissivity = 0
            min_happiness = 1
            for b in state.residences:
                b_bp = game_layer.get_residence_blueprint(b.building_name)
                if upgrade.effect not in b.effects and b.build_progress == 100:

                    if upgrade_type in ['Caretaker', 'Charger'] and b.current_pop > building_max_pop:
                        building_max_pop = b_bp.max_pop
                        actions_dict[upgrade_type] = {
                            'text': f'Upgrading {b.X, b.Y} with {upgrade_type}',
                            'callback': game_layer.buy_upgrade,
                            'args': ((b.X, b.Y), upgrade_type)
                        }

                    elif upgrade_type == 'Charger' and b.requested_energy_in > max_energy_need:
                        max_energy_need = b.requested_energy_in
                        actions_dict[upgrade_type] = {
                            'text': f'Upgrading {b.X, b.Y} with {upgrade_type}',
                            'callback': game_layer.buy_upgrade,
                            'args': ((b.X, b.Y), upgrade_type)
                        }

                    elif upgrade_type == 'Regulator' and \
                        b.requested_energy_in - b_bp.base_energy_need <= 10 and \
                            b.temperature - 21 >= max_temp_overflow:
                        max_temp_overflow = b.temperature
                        actions_dict[upgrade_type] = {
                            'text': f'Upgrading {b.X, b.Y} with {upgrade_type}',
                            'callback': game_layer.buy_upgrade,
                            'args': ((b.X, b.Y), upgrade_type)
                        }

                    elif upgrade_type == 'Insulation' and b_bp.emissivity > max_emissivity:
                        max_emissivity = b_bp.emissivity
                        actions_dict[upgrade_type] = {
                            'text': f'Upgrading {b.X, b.Y} with {upgrade_type}',
                            'callback': game_layer.buy_upgrade,
                            'args': ((b.X, b.Y), upgrade_type)
                        }

                    elif upgrade_type == 'Playground' and \
                            b_bp.max_happiness - b.happiness_per_tick_per_pop < min_happiness:
                        min_happiness = b_bp.max_happiness - b.happiness_per_tick_per_pop
                        actions_dict[upgrade_type] = {
                            'text': f'Upgrading {b.X, b.Y} with {upgrade_type}',
                            'callback': game_layer.buy_upgrade,
                            'args': ((b.X, b.Y), upgrade_type)
                        }

    return actions_dict
