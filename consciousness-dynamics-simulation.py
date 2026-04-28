import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# ====================== Consciousness Dynamics Simulation ======================
# Aligned with Consciousology v7
# Supporting Code for Discuss Section 5:
# Negentropy Efficiency, Multi-Agent Dynamic Damping, and Their Integration

N_AGENTS = 15

base_params = {
    'G0': 1.5, 'k': 0.75, 'P': 2.1, 'W': 1.4, 'K': 1.2,
    'Gp': 1.5, 'alpha': 0.10, 'M': 8, 'R': 6.5, 'f': 0.18,
    'H': 2.5, 'eta': 0.01, 'gamma': 0.06, 'beta': 0.18, 'k_fast': 5.0,
}

# Template with clear strong/medium/weak differentiation
template = {
    'k_i':    np.array([1.85, 1.65, 1.45]),
    'v_i':    np.array([2.10, 1.75, 1.45]),
    'beta_i': np.array([0.038, 0.048, 0.058]),
    'eta_neg0': np.array([0.018, 0.025, 0.035]),
    'r_s0':   np.array([0.12, 0.22, 0.35])
}

# Extend parameters with variation
multi_params = {}
np.random.seed(42)

for key, arr in template.items():
    repeats = int(np.ceil(N_AGENTS / len(arr)))
    extended = np.tile(arr, repeats)[:N_AGENTS]
    noise = np.random.uniform(-0.15, 0.15, N_AGENTS) * extended
    multi_params[key] = np.clip(extended + noise, 0.01, None)


def compute_static_consciousness(params, H, M, agent_idx):
    """Static consciousness base C_stat as described in the paper"""
    N_val = (params['G0'] + params['k'] * params['P']) * params['W'] * params['K'] * \
            params['Gp'] * multi_params['v_i'][agent_idx] * (1 + params['alpha'] * M)
    
    denominator = max(params['R'] - params['f'] * H + params['eta'], 0.5)
    return N_val / denominator


def consciousness_dynamics(t, y, params, multi_params):
    """Multi-agent dynamics aligned with paper: dC_i/dt = generation - resistance + negentropy"""
    N = N_AGENTS
    C = y[0:N].copy()
    H = y[N:2*N]
    R = y[2*N:3*N]
    r_s = y[3*N:4*N]      # social resistance r_i^(s)
    eta_neg = y[4*N:5*N]  # negentropy resistance η_neg,i

    dCdt = np.zeros(N)
    dHdt = np.zeros(N)
    dRdt = np.zeros(N)
    dr_sdt = np.zeros(N)
    deta_negdt = np.zeros(N)

    total_C = np.sum(C) + 1e-8

    for i in range(N):
        C_stat_i = compute_static_consciousness(params, H[i], params['M'], i)
        opponent_C = total_C - C[i]

        # Effective game resistance
        R_eff_i = R[i] * (1 + 0.45 * (opponent_C / (opponent_C + 20.0)))

        # Generation term
        generation = (multi_params['k_i'][i] * multi_params['v_i'][i] *
                     (1 - r_s[i]) * C_stat_i * np.exp(-params['gamma'] * params['P']) * 3.2)

        resistance_term = multi_params['beta_i'][i] * R_eff_i
        self_growth = 0.18 * np.sqrt(max(C[i], 0.8))

        dCdt[i] = generation - resistance_term + eta_neg[i] + self_growth + 0.08

        # Happiness feedback loop
        F_happy = params['beta'] * (C[i] + 1.5) * 1.5
        dHdt[i] = F_happy
        dRdt[i] = -F_happy * 2.4

        # Social resistance dynamics
        dr_sdt[i] = 0.08 * (opponent_C / (opponent_C + 20.0) - r_s[i])

        # Negentropy dynamics
        deta_negdt[i] = -0.011 * eta_neg[i] + 0.0035 * r_s[i]

        # Soft cap to prevent unrealistic explosion
        if C[i] > 80:
            dCdt[i] *= (80 / C[i]) ** 1.8

    # Low consciousness protection
    for i in range(N):
        if C[i] < 2.0:
            dCdt[i] = max(dCdt[i], 0.9)

    return np.concatenate([dCdt, dHdt, dRdt, dr_sdt, deta_negdt])


# ====================== Run Simulation ======================
DAYS = 365
t_eval = np.linspace(0, DAYS, 1001)

y0 = np.concatenate([
    np.full(N_AGENTS, 5.0),
    np.full(N_AGENTS, 4.5),
    np.full(N_AGENTS, 5.5),
    multi_params['r_s0'],
    multi_params['eta_neg0']
])

print(f"Running {DAYS}-day Multi-Agent (N={N_AGENTS}) Consciousness Simulation...")

sol = solve_ivp(consciousness_dynamics, [0, DAYS], y0,
                args=(base_params, multi_params),
                method='LSODA',
                t_eval=t_eval,
                atol=1e-8, rtol=1e-8)

if sol.success:
    C_traj = sol.y[0:N_AGENTS].T
    total_C = np.sum(C_traj, axis=1)

    final_C = C_traj[-1, :]
    top_idx = np.argsort(final_C)[::-1]

    print("\n=== SIMULATION RESULTS ===")
    print(f"Mode: Multi-Agent (N={N_AGENTS})")
    for i in range(N_AGENTS):
        print(f"Agent {i+1:2d} Final Consciousness: {final_C[i]:.2f}")

    print(f"\nTotal Final Consciousness: {total_C[-1]:.2f}")
    print(f"Total Growth Rate: {100 * (total_C[-1] / total_C[0] - 1):+.1f}%")
    print(f"Minimum Consciousness: {C_traj.min():.3f}")

    # ====================== Visualization ======================
    plt.figure(figsize=(16, 12))

    # Consciousness Trajectories
    plt.subplot(2, 2, 1)
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, N_AGENTS)))
    
    for rank, i in enumerate(top_idx[:15]):
        plt.plot(sol.t, C_traj[:, i], linewidth=2.2, 
                 label=f'Agent {i+1} ({final_C[i]:.0f})', color=colors[rank])
    
    for i in top_idx[15:]:
        plt.plot(sol.t, C_traj[:, i], linewidth=1.0, alpha=0.25, color='gray')
    
    plt.plot(sol.t, total_C, 'k--', linewidth=3.5, label=f'Total C ({total_C[-1]:.0f})')
    
    plt.xlabel('Time (days)')
    plt.ylabel('Consciousness Intensity C_i(t)')
    plt.title(f'Multi-Agent Consciousness Simulation (N={N_AGENTS}, 365 days)')
    plt.legend(fontsize=9, loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.ylim(bottom=0, top=15000)

    # Social Resistance
    plt.subplot(2, 2, 2)
    for rank, i in enumerate(top_idx[:12]):
        plt.plot(sol.t, sol.y[3*N_AGENTS + i, :], linewidth=1.8, color=colors[rank],
                 label=f'Agent {i+1}' if rank < 8 else "")
    plt.xlabel('Time (days)')
    plt.ylabel('Social Resistance r_i^s(t)')
    plt.title('Social Resistance Dynamics')
    plt.legend(fontsize=9)
    plt.grid(True, alpha=0.3)

    # Negentropy Resistance
    plt.subplot(2, 2, 3)
    for i in range(N_AGENTS):
        alpha = 0.9 if i in top_idx[:10] else 0.3
        plt.plot(sol.t, sol.y[4*N_AGENTS + i, :], linewidth=1.5, alpha=alpha)
    plt.xlabel('Time (days)')
    plt.ylabel('Negentropy Resistance η_neg,i(t)')
    plt.title('Negentropy Resistance')
    plt.grid(True, alpha=0.3)

    # Base Resistance
    plt.subplot(2, 2, 4)
    for i in range(N_AGENTS):
        alpha = 0.9 if i in top_idx[:10] else 0.3
        plt.plot(sol.t, sol.y[2*N_AGENTS + i, :], linewidth=1.5, alpha=alpha)
    plt.xlabel('Time (days)')
    plt.ylabel('Base Resistance R_i(t)')
    plt.title('Base Resistance Trajectories')
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()
