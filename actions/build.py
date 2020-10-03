import numpy as np


def get_best_available_position_to_residences(state, direction='nearest'):
    all_res_x, all_res_y = [], []
    for res in state.residences:
        all_res_x.append(res.X)
        all_res_y.append(res.Y)

    centrum_x = np.round(np.mean(all_res_x), 0)
    centrum_y = np.round(np.mean(all_res_y), 0)

    if direction == 'nearest':
        min_dist = 5000
    elif direction == 'furthest':
        max_dist = 0

    build_coord = None
    for i in range(len(state.map)):
        for j in range(len(state.map)):
            if state.map[i][j] == 0:
                dist = np.abs(i-centrum_x) + np.abs(j-centrum_y)    # manhattan distance

                if direction == 'nearest' and dist < min_dist:
                    min_dist = dist
                    build_coord = (i, j)

                elif direction == 'furthest' and dist > max_dist:
                    max_dist = dist
                    build_coord = (i, j)

    return build_coord


def building(game_layer, state, building_type):
    # Residence, Park, Mall, WindTurbine

    return_dict = {'build_progress': None, 'building_name': None, 'callback': None, 'args': None}

    # if any building is in progress, continue building
    for b in state.residences + state.utilities:

        if b.build_progress < 100:    # Keep on building
            return_dict['build_progress'] = b.build_progress
            return_dict['building_name'] = b.building_name
            return_dict['callback'] = game_layer.build
            return_dict['args'] = ((b.X, b.Y), )
            return return_dict

    if building_type in ['Residence', 'Park', 'Mall']:
        build_coord = get_best_available_position_to_residences(state, direction='nearest')
    elif building_type in ['WindTurbine']:
        build_coord = get_best_available_position_to_residences(state, direction='furthest')

    if build_coord is not None:
        nbr_turns_left = state.max_turns - state.turn     # TODO: calculate this somewhere else?
        possible_buildings_to_build = []

        if building_type == 'Residence':
            available_building_blueprints = [game_layer.get_utility_blueprint(b.building_name)
                                             for b in state.available_residence_buildings]

        elif building_type in ['Park', 'Mall', 'WindTurbine']:
            available_building_blueprints = [game_layer.get_utility_blueprint(b.building_name)
                                             for b in state.available_utility_buildings]

        for building_blueprint in available_building_blueprints:

            if building_type in ['Park', 'Mall', 'WindTurbine'] and building_type != building_blueprint.name:
                continue

            if building_blueprint.cost < state.funds and nbr_turns_left > 1.5*(100/building_blueprint.build_speed):  # TODO: check 1.5 factor
                possible_buildings_to_build.append(building_blueprint.name)

        if len(possible_buildings_to_build) > 0:
            building_to_build = np.random.choice(possible_buildings_to_build)  # TODO: Do not random this

            return_dict['build_progress'] = 0
            return_dict['building_name'] = building_to_build.building_name
            return_dict['callback'] = game_layer.place_foundation
            return_dict['args'] = (build_coord, building_to_build.building_name)

    return return_dict


