from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Material:
    name: str
    layer: str  # "surface", "underground", or "atmosphere"
    needed_process: List[
        str
    ]  # industrial processes needed to harvest this material(mining, refining, etc.)
    harvest_difficulty: float  # Base time multiplier to harvest


@dataclass
class Energy:
    name: str
    energy_source: str  # "solar", "geothermal", "chemical", "radiotrophic"
    power_output: float  # Generation rate in Watts per second (W/s)
    overheat_rate: (
        float  # Thermal impact per second (positive = heating, negative = cooling)
    )
    radiation_hazard: float  # Self-inflicted radiation damage per second to hull health


@dataclass
class Organ:
    name: str
    category: str  # "sensory", "access", "crafting", "energy", "propulsion"
    required_materials: Dict[str, int]  # e.g., {"Iron": 5, "Silicon": 2}
    required_crafting_organ: Optional[str] = (
        None  # Crafting organ needed to mold this organ
    )
    power_draw: float = 0.0  # Power consumed while operating (W/s)
    # if access organ,
    enabled_processes: List[str] = field(
        default_factory=list
    )  # the industrial processes this organ enables (mining, refining, etc.)


class Planet:
    def __init__(
        self,
        name: str,
        temperature: float,  # °C
        pressure: float,  # Atmospheres (atm)
        radiation: float,  # Rads/s
        atmosphere_type: str,
        available_materials: Dict[Material, int],  # material + quantity/availibility
        solar_efficiency: float = 0,  # the surface solor irradiance unit: W/m²
        geothermal_activity: float = 0.0,  # Heat intensity for geothermal power
    ):
        self.name = name
        self.temperature = temperature
        self.pressure = pressure
        self.radiation = radiation
        self.atmosphere_type = atmosphere_type
        self.materials = available_materials
        self.solar_efficiency = solar_efficiency
        self.geothermal_activity = geothermal_activity

    def get_material_by_name(self, name: str) -> Optional[Material]:
        for mat in self.materials:
            if mat.name == name:
                return mat
        return None


class Robot:
    def __init__(self, max_health: float = 100.0, energy_capacity: float = 500.0):
        # The robot is dead if health reaches 0 and cannot operate if energy is depleted to 0
        self.max_health = max_health
        self.current_health = max_health
        self.energy_capacity = energy_capacity
        self.energy_stored = 100.0  # Initial seed power

        self.organs: List[Organ] = []
        self.active_energy_source: Optional[Energy] = None
        self.inventory: Dict[str, int] = {}  # Raw materials collected
        self.enabled_processes: List[str] = []  # Industrial processes enabled by organs

    def add_organ(self, organ: Organ) -> None:
        """Adds an organ and unlocks any industrial processes it provides."""
        self.organs.append(organ)
        for process in organ.enabled_processes:
            if process not in self.enabled_processes:
                self.enabled_processes.append(process)

    def has_organ(self, organ_name: str) -> bool:
        return any(o.name == organ_name for o in self.organs)

    def has_process(self, process_name: str) -> bool:
        """Utility function to check if the robot can perform a required action."""
        return process_name in self.enabled_processes

    def equip_energy_source(self, energy: Energy) -> None:
        self.active_energy_source = energy

    def calculate_decay_rate(self, planet: Planet) -> float:
        """
        Calculates environmental health damage per second based on planetary hazards.
        Equipped shielding organs reduce this decay rate.
        """
        temp_delta = abs(
            planet.temperature - 20.0
        )  # Optimal operating temp around 20°C

        thermal_decay = temp_delta * 0.05
        pressure_decay = planet.pressure * 0.1
        radiation_decay = planet.radiation * 0.2

        # Self-inflicted hazards from equipped energy organs
        energy_hazards = 0.0
        if self.active_energy_source:
            energy_hazards += self.active_energy_source.radiation_hazard
            if self.active_energy_source.overheat_rate > 0:
                energy_hazards += self.active_energy_source.overheat_rate * 0.1

        total_decay = thermal_decay + pressure_decay + radiation_decay + energy_hazards

        # Apply shielding reduction if Heavy Hull organ is equipped
        if self.has_organ("Heavy Hull"):
            total_decay *= 0.5

        return max(0.1, total_decay)  # Baseline minimum wear-and-tear of 0.1 HP/s

    def tick(self, time_step: float, planet: Planet) -> None:
        """
        Advances the simulation by time_step seconds.
        Updates health, power generation, and energy consumption.
        """
        # 1. Calculate environmental decay
        decay_rate = self.calculate_decay_rate(planet)
        self.current_health -= decay_rate * time_step

        # 2. Process energy generation
        if self.active_energy_source:
            generation = self.active_energy_source.power_output * time_step

            # Match attribute name `energy_source` on Energy class
            if self.active_energy_source.energy_source == "solar":
                generation *= planet.solar_efficiency
            elif self.active_energy_source.energy_source == "geothermal":
                generation *= planet.geothermal_activity

            self.energy_stored = min(
                self.energy_capacity, self.energy_stored + generation
            )

        # 3. Process baseline organ idle power draw
        total_power_draw = sum(o.power_draw for o in self.organs) * time_step
        self.energy_stored -= total_power_draw

        # Power deficit damages robot systems
        if self.energy_stored < 0:
            self.energy_stored = 0
            self.current_health -= 2.0 * time_step  # Power failure damage penalty

    @property
    def is_alive(self) -> bool:
        return self.current_health > 0


# --- QUICK TEST DEMONSTRATION ---
if __name__ == "__main__":
    # 1. Instantiate Materials with (name, layer, needed_processes, harvest_difficulty)
    regolith = Material("Regolith", "surface", ["surface_scoop"], 1.0)
    iron = Material("Iron", "underground", ["deep_mining"], 2.5)

    # 2. Create sample planet with available_materials as Dict[Material, Quantity]
    mars = Planet(
        name="Mars",
        temperature=-60.0,
        pressure=0.006,
        radiation=0.24,
        atmosphere_type="Thin CO2",
        available_materials={regolith: 1000, iron: 150},
        solar_efficiency=0.6,
        geothermal_activity=0.1,
    )

    # 3. Create energy module & organs (including enabled_processes)
    solar_panel = Energy(
        name="Solar Wings",
        energy_source="solar",
        power_output=15.0,
        overheat_rate=0.0,
        radiation_hazard=0.0,
    )
    drill = Organ(
        name="Deep Drill",
        category="access",
        required_materials={"Iron": 2},
        power_draw=2.0,
        enabled_processes=["deep_mining"],
    )

    # 4. Assemble test robot
    probe = Robot()
    probe.equip_energy_source(solar_panel)
    probe.add_organ(drill)

    # 5. Simulate 10 seconds on Mars
    print(
        f"Initial Health: {probe.current_health:.1f} HP | Power: {probe.energy_stored:.1f} W"
    )
    print(f"Enabled Processes: {probe.enabled_processes}")

    for _ in range(10):
        probe.tick(time_step=1.0, planet=mars)

    print(
        f"Health after 10s on Mars: {probe.current_health:.1f} HP | Power: {probe.energy_stored:.1f} W"
    )
    print(f"Decay Rate: {probe.calculate_decay_rate(mars):.2f} HP/s")
