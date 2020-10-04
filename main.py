import pickle
from game_layer import GameLayer
from q_learning_algo import QLearningBase
import numpy as np
from actions import build, maintain, adjust

api_key = "c3d744bb-8484-42db-a36f-e52d86f98d29"   # TODO: Your api key here
# The different map names can be found on considition.com/rules
map_name = "training1"  # TODO: You map choice here. If left empty, the map "training1" will be selected.

game_layer = GameLayer(api_key)


def select_action(actions_q_values, eps):
    r = np.random.rand()
    if r < eps:
        action = np.random.choice(list(actions_q_values.keys()))
    else:
        action, _ = QLearningBase.get_action_and_max_q_value(actions_q_values)

    return action


def get_possible_actions_with_callback():
    build_types = ['Residence', 'Park', 'Mall', 'WindTurbine']
    action_callback_dict = dict()
    for build_type in build_types:
        rtn_dict = build.building(game_layer, build_type)
        if rtn_dict['callback'] is not None:
            action_callback_dict[f'build_{build_type}'] = rtn_dict

    rtn_dict = maintain.residence(game_layer)
    if rtn_dict['callback'] is not None:
        action_callback_dict['maintain'] = rtn_dict

    rtn_dict = adjust.heat(game_layer)
    if rtn_dict['callback'] is not None:
        action_callback_dict['adjust_heat'] = rtn_dict

    return action_callback_dict


def train(q_table, eps, verbose=False):
    game_layer.new_game(map_name)

    print("Starting game: " + game_layer.game_state.game_id)

    # init
    game_layer.start_game()
    game_state = game_layer.game_state
    q_learning = QLearningBase(q_table=q_table)

    # take turns
    while game_state.turn < game_state.max_turns:

        if verbose:
            print(f'turn: {game_state.turn}, funds: {game_state.funds}, pop: {game_state.total_population}')

        # get last turn
        prev_state_agg = game_state.aggregated_state_string(game_layer)
        prev_score = game_state.get_score()

        if prev_state_agg not in q_table:
            q_table[prev_state_agg] = dict()

        # get possible actions
        actions_callback = get_possible_actions_with_callback()
        possible_actions = list(actions_callback.keys())

        if len(possible_actions) == 0:      # TODO: Borde vi inte alltid tillåta wait?
            possible_actions.append('wait')
        for possible_action in possible_actions:
            if possible_action not in q_table:
                q_table[prev_state_agg][possible_action] = 0

        # get q vals and select action
        action_q_vals = {action: q_table[prev_state_agg][action] for action in possible_actions}
        selected_action = select_action(action_q_vals, eps)     # TODO: Implement logic to lower eps over turns

        if verbose:
            print(f'took action {selected_action}')

        if selected_action == 'wait':
            game_layer.wait()
        else:
            actions_callback[selected_action]['callback'](*actions_callback[selected_action]['args'])

            if verbose:
                print(f'action info: {actions_callback[selected_action].get("text", "nothing to say")}')

        # get new state and score
        current_state_agg = game_state.aggregated_state_string(game_layer)
        current_score = game_state.get_score()
        delta_score = current_score-prev_score

        if verbose:
            print(f'reward: {delta_score}')

        # update q_table
        if current_state_agg not in q_table:
            q_table[current_state_agg] = dict()

        q_learning.update_rule(previous_state=prev_state_agg,
                               current_state=current_state_agg,
                               selected_action=selected_action,
                               reward=delta_score)
        if verbose:
            print('--------------------------------------------')

    print("Done with game: " + game_layer.game_state.game_id)
    print("Final score was: " + str(game_layer.get_score()["finalScore"]))


def main_old():
    game_layer.new_game(map_name)
    print("Starting game: " + game_layer.game_state.game_id)
    game_layer.start_game()
    while game_layer.game_state.turn < game_layer.game_state.max_turns:
        take_turn_old()
        print('')
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


def take_turn_old():
    # TODO Implement your artificial intelligence here.
    # TODO Take one action per turn until the game ends.
    # TODO The following is a short example of how to use the StarterKit

    state = game_layer.game_state

    if len(state.residences) < 1:
        for i in range(len(state.map)):
            for j in range(len(state.map)):
                if state.map[i][j] == 0:
                    x = i
                    y = j
                    break
        game_layer.place_foundation((x, y), game_layer.game_state.available_residence_buildings[0].building_name)
    else:
        the_only_residence = state.residences[0]
        if the_only_residence.build_progress < 100:
            game_layer.build((the_only_residence.X, the_only_residence.Y))
        elif the_only_residence.health < 50:
            game_layer.maintenance((the_only_residence.X, the_only_residence.Y))
        elif the_only_residence.temperature < 18:
            blueprint = game_layer.get_residence_blueprint(the_only_residence.building_name)
            energy = blueprint.base_energy_need + 0.5 \
                     + (the_only_residence.temperature - state.current_temp) * blueprint.emissivity / 1 \
                     - the_only_residence.current_pop * 0.04
            game_layer.adjust_energy_level((the_only_residence.X, the_only_residence.Y), energy)
        elif the_only_residence.temperature > 24:
            blueprint = game_layer.get_residence_blueprint(the_only_residence.building_name)
            energy = blueprint.base_energy_need - 0.5 \
                     + (the_only_residence.temperature - state.current_temp) * blueprint.emissivity / 1 \
                     - the_only_residence.current_pop * 0.04
            game_layer.adjust_energy_level((the_only_residence.X, the_only_residence.Y), energy)
        elif state.available_upgrades[0].name not in the_only_residence.effects:
            game_layer.buy_upgrade((the_only_residence.X, the_only_residence.Y), state.available_upgrades[0].name)
        else:
            game_layer.wait()
    for message in game_layer.game_state.messages:
        print(message)
    for error in game_layer.game_state.errors:
        print("Error: " + error)


def end_games():
    from api import get_games, end_game
    games = get_games(api_key)
    for game in games:
        end_game(api_key, game['gameId'])
    print('Ended all current games')


if __name__ == "__main__":
    end_games()
    # train(dict(), 0.5)
    training_main('q_tables/q_victor_20201004.pkl', verbose=True)

