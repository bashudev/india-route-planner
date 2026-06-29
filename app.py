import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import pandas as pd

# Set up page configuration
st.set_page_config(page_title="India Route Sequence Planner", layout="wide")

st.title("🗺️ India City Sequence Route Planner")
st.write("Input between 1 and 10 Indian cities, arrange their travel sequence, and view your road trip map!")

# Initialize Geolocator for finding coordinates
geolocator = Nominatim(user_agent="india_route_planner_app")

@st.cache_data(show_spinner=False)
def get_city_coordinates(city_name):
    """Fetch coordinates specifically filtered for India to avoid global duplicates."""
    try:
        # Append ', India' to ensure the search stays within the country
        location = geolocator.geocode(f"{city_name}, India", timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except GeocoderTimedOut:
        return None
    return None

# --- STEP 1: Dynamic Inputs ---
st.sidebar.header("Step 1: Enter Cities")
num_cities = st.sidebar.number_input("How many cities?", min_value=1, max_value=10, value=3, step=1)

city_inputs = []
for i in range(int(num_cities)):
    city = st.sidebar.text_input(f"City {i+1}", value="", key=f"city_{i}")
    if city.strip():
        city_inputs.append(city.strip().title())

# --- STEP 2: Process Coordinates & Sequence ---
if city_inputs:
    valid_cities = []
    coordinates = []
    
    with st.spinner("Geocoding cities..."):
        for city in city_inputs:
            coords = get_city_coordinates(city)
            if coords:
                valid_cities.append(city)
                coordinates.append(coords)
            else:
                st.sidebar.error(f"Couldn't find coordinates for '{city}'. Please check spelling.")

    if valid_cities:
        st.subheader("Step 2: Sequence Your Itinerary")
        st.write("Drag, drop, or select the order of travel below:")
        
        # Create a dataframe to match cities with coordinates
        city_df = pd.DataFrame({"City": valid_cities, "Coords": coordinates})
        
        # Let users re-order the found cities manually
        ordered_sequence = st.multiselect(
            "Define sequence of travel (Select in order from City 1 ➔ City 2 ➔ City 3...):",
            options=valid_cities,
            default=valid_cities
        )
        
        # Re-arrange based on user sequence preference
        final_route = []
        for city in ordered_sequence:
            coord = city_df[city_df["City"] == city]["Coords"].values[0]
            final_route.append((city, coord))
            
        # --- STEP 3: Map Plotting ---
        if final_route:
            st.subheader("🗺️ Your Travel Roadmap")
            
            # Center map on the first city or India general center if empty
            center_lat = final_route[0][1][0]
            center_lon = final_route[0][1][1]
            
            # Initialize Folium Map
            m = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles="OpenStreetMap")
            
            # Trace the roadmap line connecting the sequenced cities
            route_coords = [item[1] for item in final_route]
            
            # Only draw lines if there is more than 1 city
            if len(route_coords) > 1:
                folium.PolyLine(
                    locations=route_coords,
                    color="#1f77b4",
                    weight=4,
                    opacity=0.8,
                    tooltip="Travel Route Sequence"
                ).add_to(m)
            
            # Place interactive Markers for each city with order sequence numbers
            for index, (city_name, coord) in enumerate(final_route):
                # Highlight start point vs next stops
                marker_color = "green" if index == 0 else "blue"
                if index == len(final_route) - 1 and len(final_route) > 1:
                    marker_color = "red"  # Destination
                
                folium.Marker(
                    location=coord,
                    popup=f"<b>Stop {index + 1}: {city_name}</b>",
                    tooltip=f"{index + 1}. {city_name}",
                    icon=folium.Icon(color=marker_color, icon="info-sign")
                ).add_to(m)
            
            # Display map in Streamlit app wrapper
            st_folium(m, width=900, height=600)
            
            # Show Text Itinerary Summary below
            st.info(" -> ".join([f"**({i+1}) {c[0]}**" for i, c in enumerate(final_route)]))
    else:
        st.warning("Please type a valid Indian city name in the sidebar fields.")
else:
    st.info("👈 Get started by typing city names into the sidebar input fields!")
