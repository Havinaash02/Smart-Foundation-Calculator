import streamlit as st
import math
import random

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(page_title="Foundation Design Tool", layout="wide")

default_FS_bearing = 3.0
FS_slide_req = 1.5
FS_ot_req = 2.0
settle_limit = 25.0  # mm allowable settlement


# =========================================================
# HELPER FUNCTIONS
# =========================================================
def bearing_capacity_q_ult(c, gamma, Df, B, phi):
    """Terzaghi bearing capacity formula"""
    phi_rad = math.radians(phi)

    Nc = 5.14
    if phi > 0:
        Nq = math.exp(math.pi * math.tan(phi_rad)) * (math.tan(math.radians(45 + phi / 2))) ** 2
        Ngamma = 2 * (Nq + 1) * math.tan(phi_rad)
    else:
        Nq = 1
        Ngamma = 0

    return c * Nc + gamma * Df * Nq + 0.5 * gamma * B * Ngamma


def sliding_fs(P, H, mu):
    """Sliding factor of safety"""
    return (P * mu) / H if H != 0 else 999


def overturning_fs(P, B, M):
    """Overturning factor of safety"""
    MR = P * (B / 2)
    MO = M
    return MR / MO if MO != 0 else 999


def settlement_elastic(P, B, L, Es, nu, influence_I=1.0):
    """Elastic settlement formula (simplified)"""
    A = B * L
    q = P / A
    return influence_I * q * B * (1 - nu**2) / Es


def safe_float_list(text):
    """Convert comma list into float list"""
    parts = text.split(",")
    numbers = []
    bad = []
    for x in parts:
        try:
            numbers.append(float(x.strip()))
        except:
            bad.append(x.strip())
    return numbers, bad


# =========================================================
# MAIN APP UI
# =========================================================
st.title("🏗️ Foundation Design Tool")

st.sidebar.header("Select Mode")
mode = st.sidebar.selectbox(
    "Choose Calculation",
    [
        "Bearing Capacity",
        "Settlement",
        "Sliding Check",
        "Overturning Check",
        "Full Foundation Design",
    ],
)

tab_in, tab_out, tab_notes = st.tabs(["Input", "Output", "Notes"])

# =========================================================
# MODE 1: BEARING CAPACITY
# =========================================================
if mode == "Bearing Capacity":
    with st.sidebar:
        c = st.number_input("Cohesion c (kPa)", 0.0, 999.0, 20.0)
        phi = st.number_input("Friction angle φ (deg)", 0.0, 45.0, 30.0)
        gamma = st.number_input("Unit weight γ (kN/m³)", 1.0, 30.0, 18.0)
        Df = st.number_input("Embedment depth Df (m)", 0.0, 10.0, 1.0)
        B = st.number_input("Width B (m)", 0.1, 10.0, 2.0)
        FS = st.number_input("Factor of safety", 1.0, 10.0, default_FS_bearing)

    with tab_in:
        if st.button("Calculate Bearing Capacity"):
            q_ult = bearing_capacity_q_ult(c, gamma, Df, B, phi)
            q_allow = q_ult / FS

            st.session_state.bc = {
                "q_ult": q_ult,
                "q_allow": q_allow,
            }

    with tab_out:
        if "bc" in st.session_state:
            st.subheader("Results")
            st.write(f"Ultimate capacity qᵤ = **{st.session_state.bc['q_ult']:.2f} kPa**")
            st.write(f"Allowable capacity qₐ = **{st.session_state.bc['q_allow']:.2f} kPa**")

    with tab_notes:
        st.write("Terzaghi bearing capacity equation used.")


# =========================================================
# MODE 2: SETTLEMENT
# =========================================================
elif mode == "Settlement":
    with st.sidebar:
        P = st.number_input("Load P (kN)", 0.0, 5000.0, 500.0)
        B = st.number_input("Width B (m)", 0.1, 10.0, 2.0)
        L = st.number_input("Length L (m)", 0.1, 10.0, 2.0)
        Es = st.number_input("Elastic modulus Es (kPa)", 1000.0, 100000.0, 30000.0)
        nu = st.number_input("Poisson ratio ν", 0.0, 0.49, 0.3)
        I = st.number_input("Influence factor I", 0.1, 5.0, 1.0)

    with tab_in:
        if st.button("Calculate Settlement"):
            s_m = settlement_elastic(P, B, L, Es, nu, I)
            st.session_state.settle = s_m * 1000.0

    with tab_out:
        if "settle" in st.session_state:
            st.subheader("Settlement Result")
            st.write(f"Settlement = **{st.session_state.settle:.2f} mm**")

    with tab_notes:
        st.write("Elastic settlement equation applied.")


# =========================================================
# MODE 3: SLIDING CHECK
# =========================================================
elif mode == "Sliding Check":
    with st.sidebar:
        P = st.number_input("Vertical load P (kN)", 0.0, 9999.0, 500.0)
        H = st.number_input("Horizontal load H (kN)", 0.0, 9999.0, 50.0)
        mu = st.number_input("Base friction μ", 0.0, 2.0, 0.5)
        FS_req = st.number_input("Required FS", 1.0, 5.0, FS_slide_req)

    with tab_in:
        if st.button("Check Sliding"):
            FS = sliding_fs(P, H, mu)
            st.session_state.slide = FS

    with tab_out:
        if "slide" in st.session_state:
            st.subheader("Sliding Factor of Safety")
            FS = st.session_state.slide
            st.write(f"FS = **{FS:.2f}**")
            if FS >= FS_req:
                st.success("SAFE against sliding")
            else:
                st.error("FAILS sliding check")

    with tab_notes:
        st.write("Sliding resistance = μP.")


# =========================================================
# MODE 4: OVERTURNING CHECK
# =========================================================
elif mode == "Overturning Check":
    with st.sidebar:
        P = st.number_input("Vertical load P (kN)", 0.0, 9999.0, 500.0)
        B = st.number_input("Width B (m)", 0.1, 10.0, 2.0)
        M = st.number_input("Overturning moment M (kN·m)", 0.0, 9999.0, 150.0)
        FS_req = st.number_input("Required FS", 1.0, 5.0, FS_ot_req)

    with tab_in:
        if st.button("Check Overturning"):
            FS = overturning_fs(P, B, M)
            st.session_state.ovt = FS

    with tab_out:
        if "ovt" in st.session_state:
            st.subheader("Overturning Factor of Safety")
            FS = st.session_state.ovt
            st.write(f"FS = **{FS:.2f}**")
            if FS >= FS_req:
                st.success("SAFE against overturning")
            else:
                st.error("FAILS overturning check")

    with tab_notes:
        st.write("FS = resisting moment / overturning moment.")


# =========================================================
# MODE 5: FULL FOUNDATION DESIGN (MONTE CARLO)
# =========================================================
else:
    with st.sidebar:
        st.subheader("Geometry")
        L = st.number_input("Length L (m)", 0.1, 10.0, 2.0)
        Df = st.number_input("Depth Df (m)", 0.0, 10.0, 1.0)

        st.subheader("Soil")
        c = st.number_input("Cohesion c (kPa)", 0.0, 200.0, 20.0)
        phi = st.number_input("Friction angle φ (deg)", 0.0, 45.0, 30.0)
        gamma = st.number_input("Unit weight γ (kN/m³)", 1.0, 30.0, 18.0)

        st.subheader("Loads")
        P = st.number_input("Vertical load P (kN)", 0.0, 5000.0, 500.0)
        H = st.number_input("Horizontal load H (kN)", 0.0, 5000.0, 80.0)
        M = st.number_input("Moment M (kN·m)", 0.0, 5000.0, 150.0)

        st.subheader("Stiffness")
        Es = st.number_input("Elastic modulus Es (kPa)", 1000.0, 100000.0, 30000.0)
        nu = st.number_input("Poisson ratio ν", 0.0, 0.49, 0.3)
        mu = st.number_input("Base friction μ", 0.0, 2.0, 0.5)
        I = st.number_input("Settlement influence I", 0.5, 2.0, 1.0)

        st.subheader("Monte Carlo Settings")
        B_text = st.text_input("B values (comma)", "1.5,2.0,2.5")
        iterations = st.slider("Iterations", 50, 2000, 300, 50)
        seed = st.number_input("Random seed", 0, 999999, 42)

        st.subheader("Uncertainty (%)")
        g_var = st.slider("γ variation", 0, 30, 10)
        P_var = st.slider("P variation", 0, 30, 10)
        Es_var = st.slider("Es variation", 0, 40, 15)

        st.subheader("Safety Criteria")
        FS_bearing = st.number_input("FS bearing", 1.0, 10.0, default_FS_bearing)

    with tab_in:
        if st.button("Run Full Foundation Design"):
            B_list, bad = safe_float_list(B_text)
            if not B_list:
                st.error("Invalid B list!")
            else:
                rng = random.Random(seed)
                results = []
                progress = st.progress(0.0)

                for i, B in enumerate(B_list):
                    safe_count = 0

                    for _ in range(iterations):
                        gamma_r = gamma * rng.uniform(1 - g_var / 100, 1 + g_var / 100)
                        Es_r = Es * rng.uniform(1 - Es_var / 100, 1 + Es_var / 100)
                        P_r = P * rng.uniform(1 - P_var / 100, 1 + P_var / 100)

                        # Bearing
                        q_ult = bearing_capacity_q_ult(c, gamma_r, Df, B, phi)
                        q_allow = q_ult / FS_bearing
                        q_apply = P_r / (B * L)

                        # Sliding
                        FSs = sliding_fs(P_r, H, mu)

                        # Overturning
                        FSo = overturning_fs(P_r, B, M)

                        # Settlement
                        s = settlement_elastic(P_r, B, L, Es_r, nu, I) * 1000

                        passes = (
                            (q_allow >= q_apply)
                            and (FSs >= FS_slide_req)
                            and (FSo >= FS_ot_req)
                            and (s <= settle_limit)
                        )

                        if passes:
                            safe_count += 1

                    safety_percent = (safe_count / iterations) * 100
                    results.append((B, safety_percent))

                    progress.progress((i + 1) / len(B_list))

                st.session_state.mc = results

    with tab_out:
        if "mc" in st.session_state:
            st.subheader("Monte Carlo Reliability Results")
            for B, pct in st.session_state.mc:
                st.write(f"B = **{B} m** → Reliability = **{pct:.1f}%**")
                if pct >= 80:
                    st.success("GOOD")
                else:
                    st.error("POOR")

    with tab_notes:
        st.write("Monte Carlo simulation evaluates reliability under uncertain soil + load + stiffness.")

