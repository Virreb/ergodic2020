import numpy as np


def build_building(game_layer, state):

    return_dict = {'build_progress': None, 'building_name': None}
    all_res_x, all_res_y = [], []
    for res in state.residences:

        if res.build_progress < 100:    # Keep on building  # TODO: Check in main
            game_layer.build((res.X, res.Y))
            return_dict['build_progress'] = res.build_progress
            return_dict['building_name'] = res.building_name
            return return_dict

        all_res_x.append(res.X)
        all_res_y.append(res.Y)

    centrum_x = np.round(np.mean(all_res_x), 0)
    centrum_y = np.round(np.mean(all_res_y), 0)

    min_dist = 5000
    build_coord = None
    for i in range(len(state.map)):
        for j in range(len(state.map)):
            if state.map[i][j] == 0:
                dist = np.abs(i-centrum_x) + np.abs(j-centrum_y)

                if dist < min_dist:
                    min_dist = dist
                    build_coord = (i, j)

    if build_coord is not None:

        available_building = [b for b in state.available_residence_buildings if
                              game_layer.get_residence_blueprint(b.building_name).cost < state.funds]

        if len(available_building) > 0:
            building_to_build = np.random.choice(available_building)  # TODO: Do not random this

            game_layer.place_foundation(build_coord, building_to_build.building_name)

            return_dict['build_progress'] = 0
            return_dict['building_name'] = building_to_build.building_name

    return return_dict
