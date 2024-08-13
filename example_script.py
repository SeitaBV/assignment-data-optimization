import numpy as np
import pandas as pd
from pyomo.core import (
    ConcreteModel,
    Var,
    RangeSet,
    Param,
    Reals,
    NonNegativeReals,
    NonPositiveReals,
    Binary,
    Constraint,
    Objective,
    minimize,
)
from pyomo.environ import value
from pyomo.opt import SolverFactory


def compute_soc_schedule(power_schedule, soc_start):
    """Determine the scheduled state of charge (SoC), given a power schedule and a starting SoC.

    Does not take into account conversion efficiencies.
    """
    return [soc_start] + list(np.cumsum(power_schedule) + soc_start)


def schedule_simple_battery(
    prices: pd.DataFrame,
    soc_start: float,
    soc_max: float,
    soc_min: float,
    soc_target: float,
    power_capacity: float,
    conversion_efficiency: float = 1,
):
    """Schedule a simplistic battery against given consumption and production prices.

    Solves the following optimization problem:

    $$
    \min \sum_{t=0}^{T} Price_{Buy}(t)\cdot Charge(t) - Price_{Sell}(t) \cdot Discharge(t)
    $$

    s.t.

    $$
    SOC(t) = SOC(0) + \sum_{t=0}^{T} [ \eta \cdot Charge(t) - \frac{1}{\eta} \cdot Discharge(t)]
    $$

    $$
    SOC_{min} \leq SOC(t) \leq SOC_{max}
    $$
    $$
    0 \leq Charge(t) \leq Capacity
    $$
    $$
    0 \leq Discharge(t) \leq Capacity
    $$

    :param prices:                  Pandas DataFrame with columns "consumption" and "production" containing prices.
    :param soc_start:               State of charge at the start of the schedule.
    :param soc_max:                 Maximum state of charge.
    :param soc_min:                 Minimum state of charge.
    :param soc_target:              Target state of charge at the end of the schedule.
    :param power_capacity:          Power capacity for both charging and discharging.
    :param conversion_efficiency:   Conversion efficiency from power to SoC and vice versa.
    """
    model = ConcreteModel()
    model.j = RangeSet(0, len(prices.index.to_pydatetime()) - 1, doc="Set of datetimes")
    model.ems_power = Var(model.j, domain=Reals, initialize=0)
    model.device_power_down = Var(model.j, domain=NonPositiveReals, initialize=0)
    model.device_power_up = Var(model.j, domain=NonNegativeReals, initialize=0)

    def price_up_select(m, j):
        return prices["consumption"].iloc[j]

    def price_down_select(m, j):
        return prices["production"].iloc[j]

    model.up_price = Param(model.j, initialize=price_up_select)
    model.down_price = Param(model.j, initialize=price_down_select)

    model.device_max = Param(model.j, initialize=soc_max)
    model.device_min = Param(model.j, initialize=soc_min)

    def ems_derivative_bounds(m, j):
        return (
            -power_capacity,
            m.ems_power[j],
            power_capacity,
        )

    def device_bounds(m, j):
        stock_changes = [
            (
                m.device_power_down[k] / conversion_efficiency  # -9 power out means -10 stock change
                + m.device_power_up[k] * conversion_efficiency  # 10 power in means 9 stock change
            )
            for k in range(0, j + 1)
        ]

        # Apply soc target
        if j == len(prices) - 1:
            return (
                soc_target,
                soc_start + sum(stock_changes),
                soc_target,
            )

        # Stay within SoC bounds
        return (
            m.device_min[j],
            soc_start + sum(stock_changes),
            m.device_max[j],
        )

    def device_derivative_equalities(m, j):
        """Determine aggregate flow ems_power."""
        return (
            0,
            m.device_power_up[j] + m.device_power_down[j] - m.ems_power[j],
            0,
        )

    model.device_power_up_bounds = Constraint(model.j, rule=ems_derivative_bounds)
    model.device_power_equalities = Constraint(model.j, rule=device_derivative_equalities)
    model.device_energy_bounds = Constraint(model.j, rule=device_bounds)

    # Add objective
    def cost_function(m):
        costs = 0
        for j in m.j:
            costs += m.device_power_down[j] * m.down_price[j]
            costs += m.device_power_up[j] * m.up_price[j]
        return costs

    model.costs = Objective(rule=cost_function, sense=minimize)
    solver = SolverFactory("appsi_highs")
    results = solver.solve(model, load_solutions=False)
    print(results.solver.termination_condition)

    # Load the results only if a feasible solution has been found
    if len(results.solution) > 0:
        model.solutions.load_from(results)

    planned_costs = value(model.costs)
    planned_device_power = [model.ems_power[j].value for j in model.j]

    return planned_costs, planned_device_power


raw_prices = dict(
    production=[7, 2, 3, 4, 1, 6, 7, 2, 3, 4, 1, 6, 7, 2, 3, 4, 1, 6, 7, 2, 3, 4, 1, 6],
    consumption=[8, 3, 4, 5, 2, 7, 8, 3, 4, 5, 2, 7, 8, 3, 4, 5, 2, 7, 8, 3, 4, 5, 2, 7],
)
soc_start=20
soc_max=90
soc_min=10
soc_target=90
power_capacity=10
prices = pd.DataFrame(raw_prices, index=pd.date_range("2000-01-01T00:00+01", periods=len(raw_prices["consumption"]), freq="1H", inclusive="left"))
costs, power_schedule = schedule_simple_battery(
    prices=prices,
    soc_start=soc_start,
    soc_max=soc_max,
    soc_min=soc_min,
    soc_target=soc_target,
    power_capacity=power_capacity,
)
soc_schedule = compute_soc_schedule(power_schedule, soc_start=soc_start)
print(f"Costs: {costs}")
print(f"Power schedule: {power_schedule}")
print(f"SoC schedule: {soc_schedule}")

