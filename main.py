''' Present an interactive function explorer with slider widgets.
Scrub the sliders to change the properties of the ``sin`` curve, or
type into the title text box to update the title of the plot.
Use the ``bokeh serve`` command to run the example by executing:
    bokeh serve sliders.py
at your command prompt. Then navigate to the URL
    http://localhost:5006/sliders
in your browser.
'''
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider, TextInput
from bokeh.plotting import figure
from bokeh.palettes import Spectral5, Spectral11

import pandas as pd
import numpy as np

from surface3d import Surface3d
from bokeh.driving import count

# Set up widgets
area = Slider(title="A (area)", value=0.65, start=0.05, end=2, step=0.1)
branches = Slider(title="B (branches)", value=0.73,
                  start=0.1, end=2, step=0.01)
carrying_cap = Slider(title="K (carrying capacity)",
                      value=10, start=5, end=20, step=0.1)
bug_birth_rate = Slider(title="R (birth rate)", value=0.2,
                        start=0.2, end=0.7, step=0.005)
initial_pop = Slider(title="Initial Pop.", value=5, start=1, end=100, step=1)

params1 = [initial_pop]
params2 = [area, branches]
params3 = [carrying_cap, bug_birth_rate]

source = ColumnDataSource(data=dict())
rk_source = ColumnDataSource(data=dict())
bifurc_source = ColumnDataSource(data=dict())
bifurc_source1 = ColumnDataSource(data=dict())
surface_source = ColumnDataSource(data=dict())


def predation(u):
    return u ** 2 / (1 + u ** 2)


def population(u):
    R = bug_birth_rate.value * area.value / branches.value
    K = carrying_cap.value / area.value
    return R * u * (1 - u / K) - predation(u)


def create_plot(title, x, y_series, x_label, y_label, source, circle_series):
    plot = figure(plot_height=300, plot_width=300, title=title,
                  tools="crosshair,pan,reset,save,wheel_zoom,box_zoom", output_backend="webgl")
    i = 0
    palette = Spectral5
    if len(y_series) > 5:
        palette = Spectral11

    for series in y_series:
        plot.line(x, series, source=source, line_width=3,
                  line_alpha=0.6, color=palette[i])
        i += 1

    if circle_series is True:
        plot.circle('k_pt', 'r_pt', source=bifurc_source1,
                    size=10, color="navy", alpha=0.5)
    plot.xaxis.axis_label = x_label
    plot.yaxis.axis_label = y_label
    return plot


def calc_r(u):
    return 2 * u ** 3 / (1 + u ** 2) ** 2


def calc_k(u):
    return 2 * u ** 3 / (u ** 2 - 1)


def calculate_N(n_start, T):
    N = [n_start]
    for s in T[1:]:
        start_pop = N[-1]
        n_dot = population(start_pop)
        N += [start_pop + n_dot]
    return np.array(N)


def update_data(attrname, old, new):

    # Get the current slider values
    A = area.value
    B = branches.value
    R = bug_birth_rate.value * A / B
    K = carrying_cap.value / A
    N_init = initial_pop.value

    # Generate the new curve
    new_df = pd.DataFrame()
    new_df['t'] = df['t'].copy()
    N = calculate_N(N_init, new_df['t'])

    new_df['N_dot'] = population(N)
    U = np.linspace(0, 20, len(df['t']))  # N / A
    new_df['u'] = U

    # updates for the first state space
    new_df['tau'] = B * df['t'] / A
    new_df['r'] = calc_r(U)
    new_df['k'] = calc_k(U)
    new_df['f(u)_RHS'] = U / (1 + U ** 2)
    new_df['f(u)_LHS'] = R * (1 - U / K)
    #     rk_df['t'] = df['t'].copy()new_df = new_df[new_df['u'] > 1.0]

    source.data = source.from_df(new_df)

    rk_df = pd.DataFrame()
    rk_df['t'] = df['t'].copy()
    # plot u for a range of initial population sizes
    for e in u_trajectories:
        rk_df[str(e)] = calculate_N(e, df['t'])
    # rk_df = rk_df[rk_df[[str(e) for e in u_trajectories]] > 1.0].dropna()

    # rk_df['r1'] = 2 * rk_df['u'] ** 3 / (1 + rk_df['u'] ** 2) ** 2
    # rk_df['k1'] = 2 * rk_df['u'] ** 3 / (rk_df['u'] ** 2 - 1)
    rk_source.data = rk_source.from_df(rk_df)
    bifurc_df = pd.DataFrame()
    bifurc_df['u'] = np.linspace(0, 20, 50*len(df['t']))
    bifurc_df['r'] = calc_r(bifurc_df['u'])
    bifurc_df['k'] = calc_k(bifurc_df['u'])
    bifurc_df = bifurc_df[(bifurc_df['u'] > 1) & (bifurc_df['k'] < 40)]
    # bifurc_df = bifurc_df[['r', 'k']]
    bifurc_source.data = bifurc_source.from_df(bifurc_df)

    foo = pd.DataFrame()
    foo['r_pt'] = [bug_birth_rate.value * area.value / branches.value]
    foo['k_pt'] = [carrying_cap.value / area.value]

    bifurc_source1.data = bifurc_source1.from_df(foo)

    # bifurc_source2.data = bifurc_source2.from_df(foo1)


# Set up callbacks
for w in params1 + params2 + params3:
    w.on_change('value', update_data)

# Set up dataframe
stop_time = 10

# set the initial u values (dimensionless initial population parameter)
u_trajectories = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2, 5, 10, 20]

df = pd.DataFrame()
df['t'] = np.linspace(0, stop_time, 100)

update_data(None, None, None)


plot1 = create_plot("Population Dynamics", 't', ['N_dot'], 'time (t)',
                    "N_dot (rate of change of population)", source, False)

# Set up x vs. f(x) plot
plot2 = create_plot("Transform 1", 'u',
                    ['f(u)_RHS', 'f(u)_LHS'],
                    'u', 'F(u)', source, False)


plot3 = create_plot("Stability Regions", 'k', [
                    'r'], 'k', 'r', bifurc_source, True)


# now plot the surface of the population
plot4 = create_plot("Steady States (varying initial pop.)", 't', [
                    str(e) for e in u_trajectories], 't', 'u', rk_source, False)

# Set up layouts and add to document
inputs = row(column(params1), column(params2), column(params3))

layout = row(
    column(inputs, row(plot1, plot2, plot4),
           row(plot3), width=1000),
)

curdoc().add_root(layout)

curdoc().title = "Sliders"
