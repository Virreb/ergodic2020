import api
from game_layer import GameLayer

api_key = "c3d744bb-8484-42db-a36f-e52d86f98d29"   # TODO: Your api key here
# The different map names can be found on considition.com/rules
map_name = "training1"  # TODO: You map choice here. If left empty, the map "training1" will be selected.

game_layer = GameLayer(api_key)


def main():
    game_layer.new_game(map_name)
    print("Starting game: " + game_layer.game_state.game_id)
    game_layer.start_game()
    while game_layer.game_state.turn < game_layer.game_state.max_turns:
        take_turn()
    print("Done with game: " + game_layer.game_state.game_id)
    print("Final score was: " + str(game_layer.get_score()["finalScore"]))


def take_turn():
    # TODO Implement your artificial intelligence here.
    # TODO Take one action per turn until the game ends.
    # TODO The following is a short example of how to use the StarterKit

    state = game_layer.game_state

    agg_state = get_aggregated_state(state)

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
    print('dsasd')



def get_aggregated_state(state):
    aggregated_state = {}

    # Funds
    if state.funds >= 40000:
        funds = "HIGH"
    elif 10000 < state.funds < 40000:
        funds = "MEDIUM"
    else:
        funds = "LOW"
    aggregated_state["funds"] = funds


    # Queue
    if state.housing_queue >= 30:
        housing_queue = "HIGH"
    elif 15 < state.housing_queue < 30:
        housing_queue = "MEDIUM"
    else:
        housing_queue = "LOW"
    aggregated_state["housing_queue"] = housing_queue


    # Queue Happiness
    if state.queue_happiness >= 30:
        queue_happiness = "HIGH"
    elif 15 < state.queue_happiness < 30:
        queue_happiness = "MEDIUM"
    else:
        queue_happiness = "LOW"
    aggregated_state["queue_happiness"] = queue_happiness


    # Population Capacity
    current_pop = 0
    max_capacity = 0
    for resident in state.residences:
        current_pop = current_pop + resident.current_pop
        bp = game_layer.get_residence_blueprint(resident.building_name)
        max_capacity = max_capacity + bp.max_pop
    pop_capacity = max_capacity - current_pop
    if pop_capacity >= 30:
        pop_capacity = "HIGH"
    elif 5 < pop_capacity < 30:
        pop_capacity = "MEDIUM"
    else:
        pop_capacity = "LOW"
    aggregated_state["pop_capacity"] = pop_capacity

    # Max Diff Energy
    max_energy_diff = 0
    actual_diff = 0
    for resident in state.residences:
        current_diff = resident.requested_energy_in - resident.effective_energy_in
        if abs(current_diff) > max_energy_diff:
            max_energy_diff = abs(current_diff)
            actual_diff = current_diff

    if actual_diff >= 5:
        actual_diff = "HIGH"
    elif 1 < actual_diff < 5:
        actual_diff = "MEDIUM"
    else:
        actual_diff = "LOW"
    aggregated_state["max_energy_diff"] = actual_diff

    # Min Happiness Pop Tick
    min_happiness_per_tick_pop = None
    for resident in state.residences:
        # For the first building, set the min_happiness
        if min_happiness_per_tick_pop is None:
            min_happiness_per_tick_pop = resident.happiness_per_tick_per_pop
        # For the rest of the buildings, pick the lowest.
        if resident.happiness_per_tick_per_pop < min_happiness_per_tick_pop:
            min_happiness_per_tick_pop = resident.happiness_per_tick_per_pop
    aggregated_state["min_happiness_per_tick_pop"] = min_happiness_per_tick_pop

    # Min Building Health
    building_health = []
    for resident in state.residences:
        building_health.append(resident.health)
    if len(building_health) > 0:
        if min(building_health) > 80:
            building_health = "HIGH"
        elif 40 < min(building_health) < 80:
            building_health = "MEDIUM"
        else:
            building_health = "LOW"
    else:
        building_health = "NONE"
    aggregated_state["building_health"] = building_health

    # Max Temp Diff
    max_temp_diff = 0
    actual_diff = 0
    for resident in state.residences:
        current_diff = 21 - resident.temperature
        if abs(current_diff) > max_temp_diff:
            max_temp_diff = abs(current_diff)
            actual_diff = current_diff

    if actual_diff >= 3:
        actual_diff = "HOT"
    elif -3 < actual_diff < 3:
        actual_diff = "LAGOM"
    else:
        actual_diff = "COLD"
    aggregated_state["max_temp_diff"] = actual_diff

    return aggregated_state


def aggregated_state_string(agg_state):
    agg = ''
    for key, val in agg_state.items():
        agg += f'_{key}_{val}_|'
    return agg


if __name__ == "__main__":
    main()
    #end_games()
