import numpy as np
from pprint import pprint


class QLearningBase:
    def __init__(self, q_table):
        self.q_table = q_table
        self.learning_rate = 0.1
        self.discount_factor = 0.99

    @staticmethod
    def get_action_and_max_q_value(action_values):
        best_q_val = 0
        best_action = None
        for action, q_value in action_values.items():
            if best_q_val is None:
                best_q_val = q_value
                best_action = action
            if q_value > best_q_val:
                best_action = action
                best_q_val = q_value
        return best_action, best_q_val

    def update_rule(self, previous_state, current_state, selected_action, reward):
        try:
            old_q_val = self.q_table[previous_state][selected_action]
        except KeyError:
            if selected_action not in self.q_table[previous_state]:
                self.q_table[previous_state] = {selected_action: 0}
            old_q_val = 0

        _, max_next_q_val = self.get_action_and_max_q_value(self.q_table[current_state])
        future_q_value = old_q_val + self.learning_rate * (reward + self.discount_factor * max_next_q_val - old_q_val)
        self.q_table[previous_state][selected_action] = future_q_value


class Simulate:
    def __init__(self):
        self.q_table = {"1": {'right': 0},
                   "2": {'right': 0, "left": 0},
                   "3": {'right': 0, "left": 0},
                   "4": {"left": 0}}
        self.current_state = '1'
        self.previous_state = None
        self.q_learning = QLearningBase(self.q_table)

    def get_next_state(self, action):
        if action == 'right':
            return str(int(self.current_state) + 1)
        else:
            return str(int(self.current_state) - 1)

    def reward(self, state):
        if state == "4":
            return 0
        else:
            return -1

    def step(self, eps):

        r = np.random.rand()
        if r < eps:
            action = np.random.choice(list(self.q_table[self.current_state].keys()))
        else:
            action, _ = self.q_learning.get_action_and_max_q_value(self.current_state)

        next_state = self.get_next_state(action)
        reward = self.reward(next_state)

        self.q_learning.update_rule(previous_state=self.current_state,
                                    current_state=next_state,
                                    selected_action=action,
                                    reward=reward)

        self.current_state = next_state

    def run_session(self, eps):
        while self.current_state != "4":
            self.step(eps=eps)
        pprint(self.q_table)

    def train(self, eps):
        for i in range(20):
            self.current_state = "1"
            self.run_session(eps)


if __name__ == '__main__':
    s = Simulate()
    s.train(0.8)

