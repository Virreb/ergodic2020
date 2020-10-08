
def residence(game_layer):
    state = game_layer.game_state

    order_to_demolish = ['Cabin', 'Apartments']
    return_dict = {'text': None, 'callback': None, 'args': None}
    space_left = False
    all_res_x = list()
    all_res_y = list()
    for res in state.utilities:
        all_res_x.append(res.X)
        all_res_y.append(res.Y)

    for i in range(len(state.map)):
        for j in range(len(state.map)):
            if state.map[i][j] == 0 and i not in all_res_x and j not in all_res_y:
                space_left = True
    if space_left:
        return return_dict

    for res_type in order_to_demolish:
        for b in state.residences:
            if b.can_be_demolished and b.building_name == res_type:

                return_dict = {
                    'text': f'Demolishing residence building at {(b.X, b.Y)}',
                    'callback': game_layer.demolish,
                    'args': ((b.X, b.Y), )
                }
                break

    return return_dict
