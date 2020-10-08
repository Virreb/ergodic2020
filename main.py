import pickle
from game_layer import GameLayer
from q_learning_algo import QLearning
import numpy as np
from actions import build, maintain, adjust, demolish, upgrade
from constants import *
from tqdm import tqdm
import time

from joblib import Parallel, delayed

api_key = "c3d744bb-8484-42db-a36f-e52d86f98d29"  # DICKS
#api_key = "4a958351-c215-41f9-b3f2-97630267252b" # BRUNSÅS
# The different map names can be found on considition.com/rules
map_name = "training1"  # TODO: You map choice here. If left empty, the map "training1" will be selected.

# game_layer = GameLayer(api_key)


def get_possible_actions_structure(game_layer):
    possible_actions_structure = dict()

    # wait
    possible_actions_structure['wait'] = {'callback_collection': {'callback': game_layer.wait,
                                                                  'args': None}}
    # demolish
    rtn_dict = demolish.residence(game_layer)
    if rtn_dict['callback'] is not None:
        possible_actions_structure['demolish'] = {'callback_collection': rtn_dict}

    # improve
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

    # build residence
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

    # main
    main_actions = []
    for key in ['residence', 'improve', 'demolish', 'wait']:
        if key in possible_actions_structure:
            main_actions.append(key)
    if len(main_actions) > 0:
        possible_actions_structure['main'] = {'actions': main_actions}

    return possible_actions_structure

# def train(q_table, eps, game_layer,verbose=False):

#     # main actions
#     main_actions = list()
#     for key in ['residence', 'wait', 'demolish', 'improve']:
#         if key in possible_actions_structure:
#             main_actions.append(key)
#     if len(main_actions) > 0:
#         possible_actions_structure['main'] = {'actions': main_actions}

#     return possible_actions_structure


def init_missing_states(q_table, state, pos_acts=list()):
    if state not in q_table:
        q_table[state] = dict()
    for act in pos_acts:
        if act not in q_table[state]:
            q_table[state][act] = 0


def train(game_layer, q_tables, eps=0.8, verbose=False):

    game_layer.new_game(map_name)
    time.sleep(0.1)
    print("Starting game: " + game_layer.game_state.game_id)

    # init
    game_layer.start_game()
    game_state = game_layer.game_state
    q_learning = QLearning(q_tables, eps)

    possible_actions_structure = get_possible_actions_structure(game_layer)

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
        init_missing_states(q_learning.improve_q_learning.q_tables, improve_state,
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
            print(f'turn: {game_state.turn}, funds: {round(game_state.funds, 0)}, pop: {game_state.total_population}')

        prev_score = game_state.get_score()

        action_chain, callback = q_learning.get_action_chain_with_callback(possible_actions_structure, main_state,
                                                                           residence_state, improve_state,
                                                                           utility_state, upgrade_state)
        # for ac in action_chain.keys():
        #     if verbose:
        #         print(ac, action_chain[ac].action)
        if callback['args'] is None:
            callback['callback']()
        else:
            callback['callback'](*callback['args'])

        possible_actions_structure = get_possible_actions_structure(game_layer)

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
    # game_layer.end_game()

    return q_learning


def training_main(q_tables, eps, job, verbose=False):
    game_layer = GameLayer(api_key)

    if verbose:
        print('Starting new game: ', f'{job}/4')

    q_learning = train(game_layer, q_tables, eps=eps, verbose=verbose)
    
    return q_learning


def end_games():
    from api import get_games, end_game
    games = get_games(api_key)
    for game in games:
        if game['active'] is True:
            end_game(api_key, game['gameId'])
    print('Ended all current games')


def update_q_table(q_table_list):
    tmp_states = []
    for q_table in q_table_list:
        states = tmp_states + list(q_table.keys())
    states = set(states)
    final_q_table = {}
    for state in states:
        final_q_table[state] = {}

        tmp_q_table_list = []
        for q_table in q_table_list:
            if state in q_table.keys():
                tmp_q_table_list.append(q_table)
        actions = []
        for q_table in tmp_q_table_list:
            actions = actions + list(q_table[state].keys())
        actions = set(actions)
        for action in actions:
            vals = []
            for q_table in tmp_q_table_list:
                if action in q_table[state].keys():
                    vals.append(q_table[state][action])
            final_q_table[state][action] = np.mean(vals)

    return final_q_table


if __name__ == "__main__":
    end_games()
    eps = 0.8
    eps_decline = 0.002
    JOBS = 4
    nbr_iterations = 1000
    q_tables_save_path = 'q_tables/q_tables_1.pkl'
    q_table_names = ['main', 'residence', 'improve', 'utility', 'upgrade']
    merged_q_tables = {}
    verbose = False

    for i in tqdm(range(nbr_iterations)):
        try:
            with open(q_tables_save_path, 'rb') as f:
                q_tables = pickle.load(f)
        except FileNotFoundError:
            q_tables = {key: dict() for key in q_table_names}

        q_table_list = Parallel(n_jobs=JOBS)(
            delayed(training_main)
            (q_tables, eps, job, verbose=verbose)
            for job in range(JOBS))

        for q_table_name in q_table_names:
            specific_q_tables = [q.get_q_learning_routine(q_table_name).q_table for q in q_table_list]
            merged_q_tables[q_table_name] = update_q_table(specific_q_tables)

        with open(q_tables_save_path, 'wb') as f:
            pickle.dump(merged_q_tables, f)
        
        eps -= eps*eps_decline
