from typing import List


class GameState:
    def __init__(self, map_values):
        self.game_id: str = map_values["gameId"]
        self.map_name: str = map_values["mapName"]
        self.max_turns: int = map_values["maxTurns"]
        self.max_temp: float = map_values["maxTemp"]
        self.min_temp: float = map_values["minTemp"]
        self.map: List[List[int]] = map_values["map"]
        self.energy_levels: List[EnergyLevel] = []
        for level in map_values["energyLevels"]:
            self.energy_levels.append(EnergyLevel(level))
        self.available_residence_buildings: List[BlueprintResidenceBuilding] = []
        for building in map_values["availableResidenceBuildings"]:
            self.available_residence_buildings.append(BlueprintResidenceBuilding(building))
        self.available_utility_buildings: List[BlueprintUtilityBuilding] = []
        for building in map_values["availableUtilityBuildings"]:
            self.available_utility_buildings.append(BlueprintUtilityBuilding(building))   
        self.available_upgrades: List[Upgrade] = []
        for upgrade in map_values['availableUpgrades']:
            self.available_upgrades.append(Upgrade(upgrade))
        self.effects: List[Effect] = []
        for effect in map_values['effects']:
            self.effects.append(Effect(effect))

        self.turn: int = 0
        self.funds: float = 0
        self.total_co2: float = 0
        self.total_happiness: float = 0
        self.current_temp: float = 0
        self.queue_happiness: float = 0
        self.housing_queue: int = 0
        self.residences: List[Residence] = []
        self.utilities: List[Utility] = []
        self.errors: List[str] = []
        self.messages: List[str] = []

    @property
    def total_population(self):
        total_pop = 0
        for res in self.residences:
            total_pop += res.current_pop
        return total_pop

    def get_score(self):
        return self.total_happiness/10 - self.total_co2 + self.total_population

    def update_state(self, state):
        self.turn = state['turn']
        self.funds = state['funds']
        self.total_co2 = state['totalCo2']
        self.total_happiness = state['totalHappiness']
        self.current_temp = state['currentTemp']
        self.queue_happiness = state['queueHappiness']
        self.housing_queue = state['housingQueue']
        self.residences = []
        for building in state['residenceBuildings']:
            self.residences.append(Residence(building))
        self.utilities = []
        for building in state['utilityBuildings']:
            self.utilities.append(Utility(building))
        self.errors = state['errors']
        self.messages = state['messages']

    def get_aggregated_state(self, game_layer):
        aggregated_state = {}

        # Any ongoing build progress
        ongoing_building = False
        for res in self.residences + self.utilities:
            if res.build_progress < 100:
                ongoing_building = True
                break
        aggregated_state['ongoing_building'] = ongoing_building

        # Turn
        if self.turn < 100:
            turn = 'BEGINNING'
        elif 100 <= self.turn < 500:
            turn = 'MID'
        else:
            turn = 'END'
        aggregated_state["turn"] = turn

        # Funds
        if self.funds >= 40000:
            funds = "HIGH"
        elif 10000 < self.funds < 40000:
            funds = "MEDIUM"
        else:
            funds = "LOW"
        aggregated_state["funds"] = funds

        # Queue
        if self.housing_queue >= 30:
            housing_queue = "HIGH"
        elif 15 < self.housing_queue < 30:
            housing_queue = "MEDIUM"
        else:
            housing_queue = "LOW"
        aggregated_state["housing_queue"] = housing_queue

        # Queue Happiness
        if self.queue_happiness >= 30:
            queue_happiness = "HIGH"
        elif 15 < self.queue_happiness < 30:
            queue_happiness = "MEDIUM"
        else:
            queue_happiness = "LOW"
        aggregated_state["queue_happiness"] = queue_happiness

        # Population Capacity
        current_pop = 0
        max_capacity = 0
        for resident in self.residences:
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
        for resident in self.residences:
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

        """
        # Min Happiness Pop Tick
        min_happiness_per_tick_pop = None
        for resident in self.residences:
            # For the first building, set the min_happiness
            if min_happiness_per_tick_pop is None:
                min_happiness_per_tick_pop = resident.happiness_per_tick_per_pop
            # For the rest of the buildings, pick the lowest.
            if resident.happiness_per_tick_per_pop < min_happiness_per_tick_pop:
                min_happiness_per_tick_pop = resident.happiness_per_tick_per_pop
        aggregated_state["min_happiness_per_tick_pop"] = min_happiness_per_tick_pop
        """

        # Min Building Health
        building_health = []
        for resident in self.residences:
            building_health.append(resident.health)
        if len(building_health) > 0:
            if min(building_health) > 80:
                building_health_val = "HIGH"
            elif 40 < min(building_health) < 80:
                building_health_val = "MEDIUM"
            else:
                building_health_val = "LOW"
        else:
            building_health_val = "NONE"
        aggregated_state["building_health"] = building_health_val

        # Max Temp Diff
        max_temp_diff = 0
        actual_diff = 0
        for resident in self.residences:
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

    def aggregated_state_string(self, game_layer):
        agg_state = self.get_aggregated_state(game_layer)
        agg = ''
        for key, val in agg_state.items():
            agg += f'_{key}_{val}_|'
        return agg


class EnergyLevel:
    def __init__(self, level_values):
        self.energy_threshold: int = level_values['energyThreshold']
        self.cost_per_mwh: float = level_values['costPerMwh']
        self.co2_per_mwh: float = level_values['tonCo2PerMwh']


class Blueprint:
    def __init__(self, blueprint):
        self.building_name: str = blueprint['buildingName']
        self.cost: int = blueprint['cost']
        self.co2_cost: int = blueprint['co2Cost']
        self.base_energy_need: float = blueprint['baseEnergyNeed']
        self.build_speed: int = blueprint['buildSpeed']
        self.type: str = blueprint['type']
        self.release_tick: int = blueprint.get('releaseTick', None)


class BlueprintUtilityBuilding(Blueprint):
    def __init__(self, blueprint_building):
        super().__init__(blueprint_building)
        self.effects: [str] = blueprint_building['effects']
        self.queue_increase: float = blueprint_building['queueIncrease']


class BlueprintResidenceBuilding(Blueprint):
    def __init__(self, blueprint_building):
        super().__init__(blueprint_building)
        self.max_pop: int = blueprint_building['maxPop']
        self.income_per_pop: float = blueprint_building['incomePerPop']
        self.emissivity: float = blueprint_building['emissivity']
        self.maintenance_cost: int = blueprint_building['maintenanceCost']
        self.decay_rate: float = blueprint_building['decayRate']
        self.max_happiness = blueprint_building['maxHappiness']


class Upgrade:
    def __init__(self, upgrade):
        self.name: str = upgrade['name']
        self.effect: str = upgrade['effect']
        self.cost: int = upgrade['cost']


class Effect:
    def __init__(self, effect):
        self.name: str = effect['name']
        self.radius: int = effect['radius']
        self.emissivity_multiplier: float = effect['emissivityMultiplier']
        self.decay_multiplier: float = effect['decayMultiplier']
        self.building_income_increase: float = effect['buildingIncomeIncrease']
        self.max_happiness_increase: float = effect['maxHappinessIncrease']
        self.mwh_production: float = effect['mwhProduction']
        self.base_energy_mwh_increase: float = effect['baseEnergyMwhIncrease']
        self.co2_per_pop_increase: float = effect['co2PerPopIncrease']
        self.decay_increase: float = effect['decayIncrease']


class Building:
    def __init__(self, building):
        self.building_name: str = building['buildingName']
        self.X: int = building['position']['x']
        self.Y: int = building['position']['y']
        self.effective_energy_in: float = building['effectiveEnergyIn']
        self.build_progress: int = building['buildProgress']
        self.can_be_demolished: bool = building['canBeDemolished']
        self.effects: List[str] = building['effects']


class Residence(Building):
    def __init__(self, residence):
        super().__init__(residence)
        self.current_pop: int = residence['currentPop']
        self.temperature: float = residence['temperature']
        self.requested_energy_in: float = residence['requestedEnergyIn']
        self.happiness_per_tick_per_pop: float = residence['happinessPerTickPerPop']
        self.health: int = residence['health']


class Utility(Building):
    def __init__(self, utility):
        super().__init__(utility)
