# ============================================================
# CMOS NAND Gate Simulation in PySpice
# ============================================================
# Features Included:
# - Accurate NMOS and PMOS MOSFET models
# - CMOS NAND gate implementation
# - Pulse inputs for A and B
# - Operating Point (DC) Analysis
# - DC Sweep Analysis
# - AC Analysis
# - Transient Analysis
# - Error handling for convergence issues
# - Proper grounding and unit usage
# - Advanced plotting with matplotlib
# ============================================================

from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
from PySpice.Spice.Library import SpiceLibrary
from PySpice.Probe.Plot import plot

import matplotlib.pyplot as plt
import numpy as np

# ============================================================
# Create Circuit
# ============================================================

circuit = Circuit('CMOS NAND Gate')

# ============================================================
# Power Supply
# ============================================================

VDD_VALUE = 5

# Supply voltage
circuit.V('dd', 'Vdd', circuit.gnd, VDD_VALUE @ u_V)

# ============================================================
# Input Signals
# ============================================================
# Two pulse sources:
# A switches slower
# B switches faster
# This allows all NAND logic combinations to appear
# ============================================================

circuit.PulseVoltageSource(
    'A',
    'A',
    circuit.gnd,
    initial_value=0 @ u_V,
    pulsed_value=5 @ u_V,
    rise_time=1 @ u_ns,
    fall_time=1 @ u_ns,
    pulse_width=40 @ u_ns,
    period=80 @ u_ns
)

circuit.PulseVoltageSource(
    'B',
    'B',
    circuit.gnd,
    initial_value=0 @ u_V,
    pulsed_value=5 @ u_V,
    rise_time=1 @ u_ns,
    fall_time=1 @ u_ns,
    pulse_width=20 @ u_ns,
    period=40 @ u_ns
)

# ============================================================
# CMOS NAND Gate Topology
# ============================================================
#
# PMOS Network (Parallel)
#
#       Vdd
#        |
#    ----+----
#    |       |
#   PM1     PM2
#    |       |
#    ----+----
#         |
#       Output
#
# NMOS Network (Series)
#
#      Output
#         |
#        NM1
#         |
#       node_n
#         |
#        NM2
#         |
#        GND
#
# ============================================================

# ------------------------------------------------------------
# PMOS Transistors (Parallel Pull-Up Network)
# ------------------------------------------------------------

circuit.MOSFET(
    'PM1',
    'OUT',     # Drain
    'A',       # Gate
    'Vdd',     # Source
    'Vdd',     # Bulk
    model='PMOS'
)

circuit.MOSFET(
    'PM2',
    'OUT',
    'B',
    'Vdd',
    'Vdd',
    model='PMOS'
)

# ------------------------------------------------------------
# NMOS Transistors (Series Pull-Down Network)
# ------------------------------------------------------------

circuit.MOSFET(
    'NM1',
    'OUT',
    'A',
    'N1',
    circuit.gnd,
    model='NMOS'
)

circuit.MOSFET(
    'NM2',
    'N1',
    'B',
    circuit.gnd,
    circuit.gnd,
    model='NMOS'
)

# ============================================================
# MOSFET Models
# ============================================================
# PMOS width is larger to compensate for lower mobility
# ============================================================

# NMOS Model
circuit.model(
    'NMOS',
    'nmos',
    level=1,
    kp=120e-6,
    vto=0.7,
    lambda_=0.02,
    gamma=0.37,
    phi=0.65,
    cbd=20e-15,
    cbs=20e-15,
    is_=1e-14,
    w=10e-6,
    l=1e-6
)

# PMOS Model
circuit.model(
    'PMOS',
    'pmos',
    level=1,
    kp=60e-6,
    vto=-0.7,
    lambda_=0.02,
    gamma=0.37,
    phi=0.65,
    cbd=20e-15,
    cbs=20e-15,
    is_=1e-14,
    w=20e-6,
    l=1e-6
)

# ============================================================
# Small Load Capacitor
# ============================================================
# Helps transient realism and avoids floating output issues
# ============================================================

circuit.C(
    'Load',
    'OUT',
    circuit.gnd,
    0.02 @ u_pF
)

# ============================================================
# Simulator Setup
# ============================================================

simulator = circuit.simulator(
    temperature=25,
    nominal_temperature=25
)

# ============================================================
# OPERATING POINT ANALYSIS
# ============================================================

print("================================================")
print("Operating Point Analysis")
print("================================================")

try:

    op = simulator.operating_point()

    for node in op.nodes.values():
        print(f"Node {str(node)} = {float(node):.4f} V")

except Exception as e:
    print("Operating point simulation failed:")
    print(e)

# ============================================================
# DC SWEEP ANALYSIS
# ============================================================
# Sweep input A from 0V to 5V
# ============================================================

print("\n================================================")
print("DC Sweep Analysis")
print("================================================")

try:

    dc_analysis = simulator.dc(
        VA=slice(0, 5, 0.1)
    )

    plt.figure(figsize=(8, 4))

    plt.plot(
        dc_analysis.sweep,
        dc_analysis['OUT']
    )

    plt.title('DC Sweep of CMOS NAND Gate')
    plt.xlabel('Input Voltage VA [V]')
    plt.ylabel('Output Voltage Vout [V]')
    plt.grid()

    plt.show()

except Exception as e:
    print("DC analysis failed:")
    print(e)

# ============================================================
# AC ANALYSIS
# ============================================================
# Small-signal frequency response
# ============================================================

print("\n================================================")
print("AC Analysis")
print("================================================")

try:

    ac_analysis = simulator.ac(
        start_frequency=1 @ u_Hz,
        stop_frequency=1 @ u_GHz,
        number_of_points=100,
        variation='dec'
    )

    plt.figure(figsize=(8, 4))

    gain_db = 20 * np.log10(np.abs(ac_analysis['OUT']))

    plt.semilogx(
        np.array(ac_analysis.frequency),
        gain_db
    )

    plt.title('AC Frequency Response')
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Gain [dB]')
    plt.grid()

    plt.show()

except Exception as e:
    print("AC analysis failed:")
    print(e)

# ============================================================
# TRANSIENT ANALYSIS
# ============================================================
# Observe NAND gate switching behavior
# ============================================================

print("\n================================================")
print("Transient Analysis")
print("================================================")

try:

    transient = simulator.transient(
        step_time=1 @ u_ns,
        end_time=160 @ u_ns,
        max_time=2 @ u_ns,
        use_initial_condition=True
    )

    # --------------------------------------------------------
    # Plot Input and Output Waveforms
    # --------------------------------------------------------

    plt.figure(figsize=(10, 5))

    plt.plot(
        transient.time,
        transient['A'],
        label='Input A'
    )

    plt.plot(
        transient.time,
        transient['B'],
        label='Input B'
    )

    plt.plot(
        transient.time,
        transient['OUT'],
        label='Output'
    )

    plt.title('Transient Analysis of CMOS NAND Gate')

    plt.xlabel('Time [s]')
    plt.ylabel('Voltage [V]')

    plt.legend()
    plt.grid()

    plt.show()

except Exception as e:

    print("Transient simulation failed:")
    print(e)

    print("\nAttempting relaxed convergence settings...")

    try:

        simulator.options(
            reltol=1e-4,
            abstol=1e-9,
            vntol=1e-6
        )

        transient = simulator.transient(
            step_time=1 @ u_ns,
            end_time=160 @ u_ns
        )

        print("Simulation recovered successfully.")

    except Exception as e2:

        print("Simulation still failing:")
        print(e2)

# ============================================================
# LOGIC TABLE REFERENCE
# ============================================================
#
# A  B  | OUT
# ----------------
# 0  0  |  1
# 0  1  |  1
# 1  0  |  1
# 1  1  |  0
#
# ============================================================

print("\nSimulation complete.")