import streamlit as st
import networkx as nx
from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="Classroom Steps Calculator", page_icon="👟", layout="wide"
)

# Custom CSS to improve the look and feel
st.markdown(
    """
<style>
    .stApp {
        background-color: #f0f2f6; 
    }

    .stButton>button {
        background-color: #4CAF50; 
        color: white;
        font-weight: bold;
    }

    .stSelectbox {
        background-color: white;
    }

    .results {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .stSubheader { 
        color: #333; 
        font-weight: bold; 
    }

    .stMetric {
        font-size: 24px;
    }
</style>
""",
    unsafe_allow_html=True,
)


class JSONGraphLoader:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def load(self):
        with self.file_path.open() as f:
            data = json.load(f)

        G = nx.Graph()
        for item in data:
            G.add_edge(
                str(item["classroom1"]),
                str(item["classroom2"]),
                weight=int(item["steps_between"]),
            )

        return G


@st.cache_resource
def load_graph():
    file_path = "classroom-steps-dataset.json"
    loader = JSONGraphLoader(file_path)
    return loader.load()


graph = load_graph()


def get_distance(start, end):
    try:
        return nx.shortest_path_length(graph, str(start), str(end), weight="weight")
    except nx.NetworkXNoPath:
        return "No path exists between these classrooms"


def get_unique_rooms():
    return sorted(list(graph.nodes()))


def create_route_map(visited_rooms):
    fig = go.Figure()

    for i in range(len(visited_rooms) - 1):
        start = visited_rooms[i]
        end = visited_rooms[i + 1]
        fig.add_trace(
            go.Scatter(
                x=[i, i + 1],
                y=[0, 0],
                mode="lines+markers",
                name=f"{start} to {end}",
                line=dict(width=2, color="#4CAF50"),
                marker=dict(size=10, symbol="circle"),
            )
        )

    fig.update_layout(
        title="Your Route",
        xaxis_title="Stops",
        yaxis_visible=False,
        showlegend=False,
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig


def main():
    st.title("🏫 Classroom Steps Calculator")
    st.write("Calculate the total steps and calories burned between your 4 classes today!")

    rooms = get_unique_rooms()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👤 Your Information")
        weight_kg = st.number_input(
            "Enter your weight in kilograms:", min_value=1.0, value=70.0, step=0.1
        )
        intensity = st.select_slider(
            "Select the intensity of your movement:",
            options=["low", "moderate", "high"],
        )

    with col2:
        st.subheader("🔥 Calorie Burn Rate")
        calories_per_step = {"low": 0.03, "moderate": 0.045, "high": 0.06}
        df = pd.DataFrame(
            {
                "Intensity": calories_per_step.keys(),
                "Calories per Step": calories_per_step.values(),
            }
        )
        st.table(df)

    st.subheader("🗺️ Plan Your Route")

    visited_rooms = []
    stairs_list = []

    # Make sure to only allow selecting 4 classrooms
    for i in range(4):
        col1, col2 = st.columns(2)
        with col1:
            room = st.selectbox(
                f"Select classroom {i+1}", options=rooms, key=f"room_{i}"
            )
            visited_rooms.append(room)
        with col2:
            if i < 3:  # We don't need stairs info for the last classroom
                stairs = st.checkbox(
                    f"Stairs to next classroom?", key=f"stairs_{i}"
                )
                stairs_list.append(stairs)

    if st.button("Calculate Route", key="calculate_button"):
        total_steps = 0
        total_calories = 0
        route_details = []

        st.subheader("📊 Results")
        st.plotly_chart(create_route_map(visited_rooms), use_container_width=True)

        for i in range(len(visited_rooms) - 1):
            current_room = visited_rooms[i]
            next_room = visited_rooms[i + 1]
            has_stairs = stairs_list[i]

            distance = get_distance(current_room, next_room)
            if distance == "No path exists between these classrooms":
                st.warning(f"No path exists between {current_room} and {next_room}.")
            else:
                calories_factor = calories_per_step[intensity]
                if has_stairs:
                    calories_factor *= 1.5

                total_steps += distance
                calories_burned = distance * calories_factor * weight_kg / 60
                total_calories += calories_burned
                route_details.append(
                    {
                        "From": current_room,
                        "To": next_room,
                        "Steps": distance,
                        "Calories": round(calories_burned, 2),
                        "Stairs": "Yes" if has_stairs else "No",
                    }
                )

        st.markdown('<div class="results">', unsafe_allow_html=True)
        st.subheader("🚶‍♂️ Route Details")
        st.table(pd.DataFrame(route_details))

        st.metric("Total Steps", f"{total_steps:,}")
        st.metric("Total Calories Burned", f"{total_calories:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()