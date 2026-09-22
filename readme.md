# Automata Solar Conquest

An autonomous, self-replicating Von Neumann probe simulation built in Python. Players design and deploy probe lineages to harvest planetary resources, forge modular hardware organs, and colonize celestial bodies across the Solar System.

---

## 1. System Overview & Objectives

- **Primary Objective:** Colonize as many celestial bodies as possible before the global simulation timer runs out.
- **Victory Metrics:**
  1. Total active colonies across all planets/moons.
  2. Total system-wide active probe population (tie-breaker 1).
  3. Lowest average replication time per conquered body (tie-breaker 2).
- **Defeat Condition:** Total extinction of all active probes (lineage chain broken).

---

## 2. Simulation Mechanics

### 2.1 Environmental Decay Rate

Probes endure continuous structural wear (HP loss per second) calculated from planetary hazards and equipped energy modules:

```
Decay Rate = (|T - 20| * 0.05) + (P * 0.10) + (R * 0.20) + Energy Hazards - Shielding
```

- **Minimum Wear:** `0.10 HP/s` baseline decay rate.
- **Shielding:** Equip structural organs (e.g., `Heavy Hull`) to reduce total incoming decay by 50%.

### 2.2 Energy Balance

Power (ΔE) updates every tick based on environmental efficiency and total active organ consumption:

```
ΔE = (Base Output * Env Multiplier) - Σ Organ Power Draws
```

- **Solar Generation:** Multiplied by `planet.solar_efficiency`.
- **Geothermal Generation:** Multiplied by `planet.geothermal_activity`.
- **Power Deficit Penalty:** If `energy_stored` drops to 0, the probe takes an additional **2.0 HP/s penalty** due to critical power failure.

---

## 3. Data Models (`models.py`)

### `Material`

Defines raw elements and compounds found on planets.

```python
@dataclass
class Material:
    name: str                  # e.g., "Iron Ore"
    layer: str                 # "surface", "underground", or "atmosphere"
    needed_process: List[str]  # Required processes (e.g., ["deep_mining"])
    harvest_difficulty: float  # Base time multiplier
```

### `Energy`

Generates power and introduces thermal or radioactive side effects.

```python
@dataclass
class Energy:
    name: str
    energy_source: str         # "solar", "geothermal", "chemical", "radiotrophic"
    power_output: float        # Base generation in W/s
    overheat_rate: float       # Thermal impact per second
    radiation_hazard: float    # Self-inflicted radiation damage per second
```

### `Organ`

Modular hardware components attached to probes to grant capabilities or unlock processes.

```python
@dataclass
class Organ:
    name: str
    category: str                       # "sensory", "access", "crafting", "energy", "propulsion"
    required_materials: Dict[str, int]  # Cost to mold (e.g., {"Iron": 5})
    required_crafting_organ: Optional[str] = None
    power_draw: float = 0.0             # Continuous operational power draw (W/s)
    enabled_processes: List[str] = field(default_factory=list)  # Granted processes
```

### `Planet`

Stores planetary environmental attributes and material distribution.

```python
class Planet:
    def __init__(
        self,
        name: str,
        temperature: float,        # °C
        pressure: float,           # atm
        radiation: float,          # Rads/s
        atmosphere_type: str,      # e.g., "Thin CO2"
        available_materials: Dict[Material, int],  # Material -> Quantity
        solar_efficiency: float = 0.0,              # W/m² surface irradiance
        geothermal_activity: float = 0.0            # Multiplier (0.0 to 1.0)
    )
```

### `Robot`

Manages probe state, health decay, power levels, inventory, and equipped organs.

```python
class Robot:
    def __init__(self, max_health: float = 100.0, energy_capacity: float = 500.0):
        self.max_health = max_health
        self.current_health = max_health
        self.energy_capacity = energy_capacity
        self.energy_stored = 100.0
        self.organs: List[Organ] = []
        self.active_energy_source: Optional[Energy] = None
        self.inventory: Dict[str, int] = {}
        self.enabled_processes: List[str] = []
```

---

## 4. Operational Flow

```
[1. SENSE]    Read planetary telemetry (temperature, pressure, materials).
[2. EVALUATE] Match needed target organ requirements against local resources.
[3. HARVEST]  Run access organs to mine/refine raw materials into inventory.
[4. MOLD]     Use crafting organs to forge child components.
[5. LAUNCH]   Attach components + propulsion organ to new chassis and seed target planet.
```

---

## 5. Quickstart Example

```python
from models import Material, Energy, Organ, Planet, Robot

# 1. Define materials and environment
regolith = Material("Regolith", "surface", ["surface_scoop"], 1.0)
iron = Material("Iron", "underground", ["deep_mining"], 2.5)

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

# 2. Equip probe
solar_panel = Energy("Solar Wings", "solar", power_output=15.0, overheat_rate=0.0, radiation_hazard=0.0)
drill = Organ("Deep Drill", category="access", required_materials={"Iron": 2}, power_draw=2.0, enabled_processes=["deep_mining"])

probe = Robot()
probe.equip_energy_source(solar_panel)
probe.add_organ(drill)

# 3. Tick simulation
probe.tick(time_step=1.0, planet=mars)
print(f"Health: {probe.current_health:.1f} HP | Power: {probe.energy_stored:.1f} W")
```
