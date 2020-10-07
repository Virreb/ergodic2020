import pickle
from game_layer import GameLayer
from q_learning_algo import QLearning
import numpy as np
from actions import build, maintain, adjust, demolish, upgrade
from constants import *

api_key = "c3d744bb-8484-42db-a36f-e52d86f98d29"   # TODO: Your api key here
# The different map names can be found on considition.com/rules
map_name = "training1"  # TODO: You map choice here. If left empty, the map "training1" will be selected.

game_layer = GameLayer(api_key)


def get_possible_actions_structure():
    possible_actions_structure = dict()

    possible_actions_structure['wait'] = {'callback_collection': {'callback': game_layer.wait,
                                                                  'args': None}}

    rtn_dict = demolish.residence(game_layer)
    if rtn_dict['callback'] is not None:
        possible_actions_structure['demolish'] = {'callback_collection': rtn_dict}


    #improve
    rtn_dict = maintain.residence(game_layer)
    if rtn_dict['callback'] is not None:
        possible_actions_structure['maintain'] = {'callback_collection': rtn_dict}

    rtn_dict = adjust.heat(game_layer)
    if rtn_dict['callback'] is not None:
        possible_actions_structure['adjust_energy'] = {'callback_collection': rtn_dict}

    # loop over utilities
    for utility_type in ALL_UTILITY_BUILDING_NAMES:
        rtn_dict = build.building(game_layer, utility_type)
        if len(rtn_dict) > 0:

            if rtn_dict['callback'] is not None:

                if 'utility' not in possible_actions_structure:
                    possible_actions_structure['utility'] = dict()
                if 'callback_collection' not in possible_actions_structure['utility']:
                    possible_actions_structure['utility']['callback_collection'] = dict()

                possible_actions_structure['utility']['callback_collection'][utility_type] = rtn_dict

    # upgrade
    upgrade_dict = upgrade.do(game_layer)
    if len(upgrade_dict) > 0:
        possible_actions_structure['upgrade'] = {'callback_collection': upgrade_dict}

    # residence
    build_dict = build.building(game_layer, 'Residence')
    if len(build_dict) > 0:
        possible_actions_structure['residence'] = {'callback_collection': build_dict}


    # improve actions
    improve_actions = list()
    for key in ['utiltiy', 'maintain', 'upgrade', 'adjust_energy']:
        if key in possible_actions_structure:
            improve_actions.append(key)
    if len(improve_actions) > 0:
        possible_actions_structure['improve'] = {'actions': improve_actions}

    # main actions
    main_actions = list()
    for key in ['residence', 'wait', 'demolish', 'improve']:
        if key in possible_actions_structure:
            main_actions.append(key)
    if len(main_actions) > 0:
        possible_actions_structure['main'] = {'actions': main_actions}

    return possible_actions_structure


def init_missing_states(q_table, state, pos_acts=list()):
    if state not in q_table:
        q_table[state] = dict()
    for act in pos_acts:
        if act not in q_table[state]:
            q_table[state][act] = 0

def train(main_q_table, residence_q_table, improve_q_table, utility_q_table, upgrade_q_table, eps, verbose=False):
    game_layer.new_game(map_name)

    print("Starting game: " + game_layer.game_state.game_id)

    # init
    game_layer.start_game()
    game_state = game_layer.game_state
    q_learning = QLearning(main_q_table, residence_q_table, improve_q_table, utility_q_table, upgrade_q_table, eps)

    possible_actions_structure = get_possible_actions_structure()

    main_state = game_state.get_state_string(game_layer, 'main')
    residence_state = game_state.get_state_string(game_layer, 'residence')
    improve_state = game_state.get_state_string(game_layer, 'improve')
    utility_state = game_state.get_state_string(game_layer, 'utility')
    upgrade_state = game_state.get_state_string(game_layer, 'upgrade')

    init_missing_states(q_learning.main_q_learning.q_table, main_state,
                        pos_acts=possible_actions_structure['main']['actions'])
    if 'residence' in possible_actions_structure:
        init_missing_states(q_learning.residence_q_learning.q_table, residence_state,
                            pos_acts=list(possible_actions_structure['residence']['callback_collection'].keys()))
    if 'improve' in possible_actions_structure:
        init_missing_states(q_learning.improve_q_learning.q_table, improve_state,
                            pos_acts=possible_actions_structure['improve']['actions'])
    if 'utility' in possible_actions_structure:
        init_missing_states(q_learning.utility_q_learning.q_table, utility_state,
                            pos_acts=list(possible_actions_structure['utility']['callback_collection'].keys()))
    if 'upgrade' in possible_actions_structure:
        init_missing_states(q_learning.upgrade_q_learning.q_table, upgrade_state,
                            pos_acts=list(possible_actions_structure['upgrade']['callback_collection'].keys()))

    # take turns
    while game_state.turn < game_state.max_turns:

        if verbose:
            print(f'turn: {game_state.turn}, funds: {game_state.funds}, pop: {game_state.total_population}')

        prev_score = game_state.get_score()


        action_chain, callback = q_learning.get_action_chain_with_callback(possible_actions_structure, main_state,
                                                                           residence_state, improve_state,
                                                                           utility_state, upgrade_state)
        for ac in action_chain.keys():
            print(ac, action_chain[ac].action)
        if callback['args'] is None:
            callback['callback']()
        else:
            callback['callback'](*callback['args'])

        possible_actions_structure = get_possible_actions_structure()

        main_state = game_state.get_state_string(game_layer, 'main')
        residence_state = game_state.get_state_string(game_layer, 'residence')
        improve_state = game_state.get_state_string(game_layer, 'improve')
        utility_state = game_state.get_state_string(game_layer, 'utility')
        upgrade_state = game_state.get_state_string(game_layer, 'upgrade')

        init_missing_states(q_learning.main_q_learning.q_table, main_state,
                            pos_acts=possible_actions_structure['main']['actions'])
        if 'residence' in possible_actions_structure:
            init_missing_states(q_learning.residence_q_learning.q_table, residence_state,
                                pos_acts=list(possible_actions_structure['residence']['callback_collection'].keys()))
        if 'improve' in possible_actions_structure:
            init_missing_states(q_learning.improve_q_learning.q_table, improve_state,
                                pos_acts=possible_actions_structure['improve']['actions'])
        if 'utility' in possible_actions_structure:
            init_missing_states(q_learning.utility_q_learning.q_table, utility_state,
                                pos_acts=list(possible_actions_structure['utility']['callback_collection'].keys()))
        if 'upgrade' in possible_actions_structure:
            init_missing_states(q_learning.upgrade_q_learning.q_table, upgrade_state,
                                pos_acts=list(possible_actions_structure['upgrade']['callback_collection'].keys()))

        if verbose:
            print(f'action info: {callback.get("text", "nothing to say")}')

        current_score = game_state.get_score()
        delta_score = current_score - prev_score

        for key, collection in action_chain.items():
            collection.current_state = game_state.get_state_string(game_layer, key)

        q_learning.update_tables(action_chain, delta_score)

        if verbose:
            print('--------------------------------------------')

    print("Done with game: " + game_layer.game_state.game_id)
    print("Final score was: " + str(game_layer.get_score()["finalScore"]))


def training_main(q_table_name=None, verbose=False):
    try:
        with open(q_table_name, 'rb') as f:
            q_table = pickle.load(f)
    except FileNotFoundError:
        q_table = dict()

    train(q_table, 0.5, verbose=verbose)

    if q_table_name is not None:
        with open(q_table_name, 'wb') as f:
            pickle.dump(q_table, f)


def end_games():
    from api import get_games, end_game
    games = get_games(api_key)
    for game in games:
        end_game(api_key, game['gameId'])
    print('Ended all current games')


if __name__ == "__main__":
    end_games()
    # train(dict(), 0.5)
    #training_main('q_tables/q_victor_20201004.pkl', verbose=True)
    train(main_q_table=dict(), residence_q_table=dict(), improve_q_table=dict(), utility_q_table=dict(),
          upgrade_q_table=dict(), eps=0.8, verbose=True)
