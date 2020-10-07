import numpy as np
from constants import *
from math import ceil


def inside_effect_radius_for_same_building_type(state, x, y, building_type):
    # loop over all utilities, if the same building type (mall or park) is within effect radius, do not build
    for b in state.utilities:
        if b.building_name == building_type:
            dist = np.abs(b.X - x) + np.abs(b.Y - y)  # manhattan distance

            if dist <= EFFECT_RADIUS[building_type]:
                return True

    return False


def get_best_available_position_to_residences(state, building_type, direction='nearest'):
    all_res_x, all_res_y = [], []
    if len(state.residences) == 0:
        centrum_x = len(state.map)//2
        centrum_y = centrum_x
    else:
        for res in state.residences:
            all_res_x.append(res.X)
            all_res_y.append(res.Y)

        centrum_x = np.round(np.mean(all_res_x), 0)
        centrum_y = np.round(np.mean(all_res_y), 0)

    for res in state.utilities:
        all_res_x.append(res.X)
        all_res_y.append(res.Y)

    if direction == 'nearest':
        min_dist = 5000
    elif direction == 'furthest':
        max_dist = 0

    build_coord = None
    for i in range(len(state.map)):
        for j in range(len(state.map)):
            if state.map[i][j] == 0 and i not in all_res_x and j not in all_res_y:
                dist = np.abs(i-centrum_x) + np.abs(j-centrum_y)    # manhattan distance

                # if within effect radius, try next placement
                if building_type in ALL_UTILITY_BUILDING_NAMES and \
                        inside_effect_radius_for_same_building_type(state, i, j, building_type):
                    continue

                if direction == 'nearest' and dist < min_dist:
                    min_dist = dist
                    build_coord = (i, j)

                elif direction == 'furthest' and dist > max_dist:
                    max_dist = dist
                    build_coord = (i, j)

    return build_coord


def get_callbacks_for_available_residences(game_layer, build_coord, available_buildings):
    # TODO: Implement better logic here

    actions_dict = {}
    for b in available_buildings:
        actions_dict[b] = {
            'text': f'Starting to build a new residence: {b}',
            'callback': game_layer.place_foundation,
            'args': (build_coord, b)
        }

    return actions_dict


def building(game_layer, building_type):
    state = game_layer.game_state
    # Residence, Park, Mall, WindTurbine

    return_dict = {'text': None, 'callback': None, 'args': None}

    # only build one sort of building at the time (only that action can be visible)
    if building_type == 'Residence':
        # check if any utility building in progress, then return none
        for b in state.utilities:
            if b.build_progress < 100:
                return return_dict

        current_buildings = state.residences

    elif building_type in [b.building_name for b in state.available_utility_buildings]:

        # Check if any residence building or other utility building in progress, then return None
        for b in state.residences + state.utilities:
            if (b.building_name in ALL_RESIDENCE_BUILDING_NAMES or b.building_name != building_type) \
                    and b.build_progress < 100:
                return return_dict

        current_buildings = [b for b in state.utilities if b.building_name == building_type]

    for b in current_buildings:

        if b.build_progress < 100:    # Keep on building
            progress = b.build_progress + game_layer.get_blueprint(b.building_name).build_speed
            return_dict['text'] = f'Building: {b.building_name} - {progress}%'
            return_dict['callback'] = game_layer.build
            return_dict['args'] = ((b.X, b.Y), )
            return {b.building_name: return_dict}

    build_coord = get_best_available_position_to_residences(state, building_type, direction='nearest')
    # if building_type in ['Residence', 'Park', 'Mall']:
    #     build_coord = get_best_available_position_to_residences(state, building_type, direction='nearest')
    # elif building_type in ['WindTurbine']:
    #     build_coord = get_best_available_position_to_residences(state, building_type, direction='furthest')

    if build_coord is not None:
        nbr_turns_left = state.max_turns - state.turn
        possible_buildings_to_build = []

        if building_type == 'Residence':
            available_building_blueprints = [game_layer.get_residence_blueprint(b.building_name)
                                             for b in state.available_residence_buildings]

        elif building_type in ALL_UTILITY_BUILDING_NAMES:
            available_building_blueprints = [game_layer.get_utility_blueprint(b.building_name)
                                             for b in state.available_utility_buildings]

        for building_blueprint in available_building_blueprints:
            nbr_turns_to_build = ceil(100/building_blueprint.build_speed)   # round up

            if building_type in ALL_UTILITY_BUILDING_NAMES and building_type != building_blueprint.building_name:
                continue

            if building_blueprint.cost < state.funds and \
                    nbr_turns_left > NBR_TURNS_LEFT_FACTOR*nbr_turns_to_build:  # TODO: check 1.5 factor
                possible_buildings_to_build.append(building_blueprint.building_name)

        if len(possible_buildings_to_build) > 0:

            if building_type == 'Residence':
                return_dict = get_callbacks_for_available_residences(game_layer, build_coord,
                                                                     possible_buildings_to_build)

            elif building_type in ALL_UTILITY_BUILDING_NAMES:
                action = possible_buildings_to_build[0]  # there will only be one here

                return_dict['text'] = f'Starting to build new: {action}'
                return_dict['callback'] = game_layer.place_foundation
                return_dict['args'] = (build_coord, action)

    return return_dict


