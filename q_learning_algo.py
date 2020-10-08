import numpy as np
from pprint import pprint


class QLearningBase:
    def __init__(self, q_table):
        self.q_table = q_table
        self.learning_rate = 0.1
        self.discount_factor = 0.99

    @staticmethod
    def get_action_and_max_q_value(action_values):
        best_q_val = None
        best_action = None
        for action, q_value in action_values.items():
            if best_q_val is None:
                best_q_val = q_value
                best_action = action
            if q_value > best_q_val:
                best_action = action
                best_q_val = q_value
        if best_q_val is None:
            best_q_val = 0
        return best_action, best_q_val

    def update_rule(self, previous_state, current_state, selected_action, reward):
        try:
            old_q_val = self.q_table[previous_state][selected_action]
        except KeyError:
            if selected_action not in self.q_table[previous_state]:
                self.q_table[previous_state] = {selected_action: 0}
            old_q_val = 0

        try:
            _, max_next_q_val = self.get_action_and_max_q_value(self.q_table[current_state])
        except KeyError:
            max_next_q_val = 0
        future_q_value = old_q_val + self.learning_rate * (reward + self.discount_factor * max_next_q_val - old_q_val)
        self.q_table[previous_state][selected_action] = future_q_value


class StateActionCollection:
    def __init__(self, previous_state, current_state, action):
        self.previous_state = previous_state
        self.current_state = current_state
        self.action = action


def select_action(actions_q_values, eps):
    r = np.random.rand()
    if r < eps:
        action = np.random.choice(list(actions_q_values.keys()))
    else:
        action, _ = QLearningBase.get_action_and_max_q_value(actions_q_values)

    return action


class QLearning:
    def __init__(self, main_q_table, residence_q_table, improve_q_table, utility_q_table, upgrade_q_table, eps):
        self.main_q_learning = QLearningBase(main_q_table)
        self.residence_q_learning = QLearningBase(residence_q_table)
        self.improve_q_learning = QLearningBase(improve_q_table)
        self.utility_q_learning = QLearningBase(utility_q_table)
        self.upgrade_q_learning = QLearningBase(upgrade_q_table)
        self.eps = eps

    def get_q_learning_routine(self, key) -> QLearningBase:
        if key == 'main':
            return self.main_q_learning
        elif key == 'residence':
            return self.residence_q_learning
        elif key == 'improve':
            return self.improve_q_learning
        elif key == 'utility':
            return self.utility_q_learning
        elif key == 'upgrade':
            return self.upgrade_q_learning
        else:
            raise RuntimeError(f'key {key} not supported')

    def update_tables(self, action_chain, reward):
        for key, collection in action_chain.items():
            q_learning_routine = self.get_q_learning_routine(key)
            q_learning_routine.update_rule(previous_state=collection.previous_state,
                                           current_state=collection.current_state,
                                           selected_action=collection.action,
                                           reward=reward)

    def get_action(self, list_of_possible_actions, routine_type, state):
        q_learning_routine = self.get_q_learning_routine(routine_type)
        action_q_vals = {action: q_learning_routine.q_table[state][action] for action in list_of_possible_actions}
        main_action = select_action(action_q_vals, self.eps)
        return main_action

    def get_action_chain_with_callback(self,
                                       possible_action_structure,
                                       main_state,
                                       residence_state,
                                       improve_state,
                                       utility_state,
                                       upgrade_state):
        action_chain = dict()
        possible_actions = possible_action_structure['main']['actions']
        main_action = self.get_action(possible_actions, 'main', main_state)
        action_chain['main'] = StateActionCollection(previous_state=main_state,
                                                     action=main_action,
                                                     current_state=None)

        if main_action == 'residence':
            possible_actions = list(possible_action_structure['residence']['callback_collection'].keys())
            residence_action = self.get_action(possible_actions, 'residence', residence_state)
            action_chain['residence'] = StateActionCollection(previous_state=residence_state,
                                                              action=residence_action,
                                                              current_state=None)
            callback_collection = possible_action_structure['residence']['callback_collection'][residence_action]

        elif main_action == 'improve':
            possible_actions = possible_action_structure['improve']['actions']
            improve_action = self.get_action(possible_actions, 'improve', improve_state)
            action_chain['improve'] = StateActionCollection(previous_state=improve_state,
                                                            action=improve_action,
                                                            current_state=None)

            if improve_action == 'utility':
                possible_actions = list(possible_action_structure['utility']['callback_collection'].keys())
                utility_action = self.get_action(possible_actions, 'utility', utility_state)
                action_chain['utility'] = StateActionCollection(previous_state=utility_state,
                                                                action=utility_action,
                                                                current_state=None)
                callback_collection = possible_action_structure['utility']['callback_collection'][utility_action]

            elif improve_action == 'maintain':
                callback_collection = possible_action_structure['maintain']['callback_collection']
            elif improve_action == 'upgrade':
                possible_actions = list(possible_action_structure['upgrade']['callback_collection'].keys())
                upgrade_action = self.get_action(possible_actions, 'upgrade', upgrade_state)

                action_chain['upgrade'] = StateActionCollection(previous_state=upgrade_state,
                                                                action=upgrade_action,
                                                                current_state=None)
                callback_collection = possible_action_structure['upgrade']['callback_collection'][upgrade_action]

            elif improve_action == 'adjust_energy':#
                callback_collection = possible_action_structure['adjust_energy']['callback_collection']
            else:
                raise RuntimeError(f'improve action {improve_action} not valid')
        elif main_action == 'demolish':
            callback_collection = possible_action_structure['demolish']['callback_collection']
        elif main_action == 'wait':
            callback_collection = possible_action_structure['wait']['callback_collection']
        else:
            raise RuntimeError(f'main action {main_action} is not a valid main action')

        return action_chain, callback_collection

