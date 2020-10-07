
def residence(game_layer):
    state = game_layer.state

    order_to_demolish = ['Cabin', 'Apartments']
    return_dict = {'text': None, 'callback': None, 'args': None}
    for res_type in order_to_demolish:
        for b in state.residences:
            if b.can_be_demolished and b.building_name == res_type:

                return_dict = {
                    'text': f'Demolishing residence building at {(b.X, b.Y)}',
                    'callback': game_layer.demolish(),
                    'args': (b.X, b.Y)
                }
                break

    return return_dict
