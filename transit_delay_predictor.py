# Import libraries
import streamlit as st  # Web app framework
import pandas as pd     # Data handling
import random          # Random numbers
from datetime import datetime  # Time functions

# Page setup
st.set_page_config(
    page_title="🚌 Bus Delay Predictor",
    page_icon="🚌",
    layout="wide"
)

# Load bus data from CSV files
@st.cache_data  # Cache for better performance
def load_bus_data():
    """Load bus route and stop data"""
    try:
        routes = pd.read_csv('GRT_Routes (1).csv')
        stops = pd.read_csv('GRT_Stops (1).csv')
        return routes, stops
    except:
        st.error("❌ Could not find the CSV files! Make sure they're in the same folder.")
        return None, None

# Simulate weather conditions
def get_current_weather():
    """Get random weather and its delay impact"""
    weather_options = [
        ("☀️ Sunny", 1.0),           # No delay
        ("☁️ Cloudy", 1.1),          # 10% more delay  
        ("🌧️ Light Rain", 1.3),      # 30% more delay
        ("⛈️ Heavy Rain", 1.6),       # 60% more delay
        ("❄️ Snow", 1.8),            # 80% more delay
        ("🧊 Ice/Freezing", 2.0)     # 100% more delay
    ]
    
    weather_name, delay_factor = random.choice(weather_options)
    return weather_name, delay_factor

# Check if it's rush hour
def is_rush_hour():
    """Check if current time is rush hour"""
    current_hour = datetime.now().hour
    
    # Rush hour: 7-9 AM and 4-6 PM
    if (7 <= current_hour <= 9) or (16 <= current_hour <= 18):
        return True, "⏰ Rush Hour", 1.4  # 40% more delay
    else:
        return False, "😌 Regular Time", 1.0  # Normal delay

# Calculate bus delay
def predict_delay(route_number, route_name, route_length):
    """Calculate expected bus delay"""
    
    # Base delay: longer routes = more delays
    base_delay = route_length * 0.3  # 0.3 minutes per km
    
    # Get weather and time factors
    weather, weather_factor = get_current_weather()
    is_rush, time_period, time_factor = is_rush_hour()
    
    # Add random factors (construction, accidents, etc.)
    random_factor = random.uniform(0.7, 1.8)
    
    # Calculate total delay
    total_delay = base_delay * weather_factor * time_factor * random_factor
    delay_minutes = round(total_delay)
    
    return {
        'delay_minutes': delay_minutes,
        'weather': weather,
        'weather_factor': weather_factor,
        'time_period': time_period,
        'time_factor': time_factor,
        'base_delay': round(base_delay, 1),
        'is_rush': is_rush
    }

# Main app
def main():
    # App title
    st.title("🚌 Waterloo Region Bus Delay Predictor")
    st.write("Find out how late your bus might be today!")
    
    # Load data
    routes_data, stops_data = load_bus_data()
    
    if routes_data is None:
        st.stop()  # Stop if no data
    
    # Sidebar info
    st.sidebar.header("📊 Data Info")
    st.sidebar.write(f"📍 Total bus routes: {len(routes_data)}")
    st.sidebar.write(f"🚏 Total bus stops: {len(stops_data)}")
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("🔍 Select Your Bus Route")
        
        # Prepare route options
        unique_routes = routes_data[['Route', 'FullName']].drop_duplicates()
        unique_routes = unique_routes.sort_values('Route')
        
        route_options = {}
        for _, row in unique_routes.iterrows():
            route_options[f"Route {row['Route']} - {row['FullName']}"] = row['Route']
        
        # Route selection dropdown
        selected_route_text = st.selectbox(
            "Choose your bus route:",
            options=list(route_options.keys()),
            help="Pick the bus route you want to take"
        )
        
        selected_route = route_options[selected_route_text]
        
        # Predict button
        if st.button("🔮 Predict My Bus Delay!", type="primary"):
            # Get route info
            route_info = routes_data[routes_data['Route'] == selected_route].iloc[0]
            route_name = route_info['FullName']
            route_length = route_info['Length']
            
            # Make prediction
            prediction = predict_delay(selected_route, route_name, route_length)
            
            # Store in session state
            st.session_state.prediction = prediction
            st.session_state.route_info = {
                'number': selected_route,
                'name': route_name,
                'length': route_length
            }
    
    with col2:
        st.header("📈 Current Conditions")
        
        # Current time
        current_time = datetime.now().strftime("%I:%M %p")
        st.metric("🕐 Current Time", current_time)
        
        # Rush hour status
        is_rush, time_period, time_factor = is_rush_hour()
        rush_color = "🔴" if is_rush else "🟢"
        st.metric("⏰ Traffic Status", f"{rush_color} {time_period}")
        
        # Weather
        weather, weather_factor = get_current_weather()
        st.metric("🌤️ Weather Impact", weather)
    
    # Show prediction results
    if 'prediction' in st.session_state:
        st.header("🎯 Your Bus Delay Prediction")
        
        prediction = st.session_state.prediction
        route_info = st.session_state.route_info
        
        # Determine delay status
        delay = prediction['delay_minutes']
        if delay <= 2:
            status_color = "🟢"
            status_text = "ON TIME"
        elif delay <= 5:
            status_color = "🟡"
            status_text = "SLIGHTLY LATE"
        elif delay <= 10:
            status_color = "🟠"
            status_text = "MODERATELY LATE"
        else:
            status_color = "🔴"
            status_text = "VERY LATE"
        
        # Display delay
        st.metric(
            label=f"{status_color} Route {route_info['number']} - {route_info['name']}",
            value=f"{delay} minutes late",
            delta=f"Status: {status_text}"
        )
        
        # Explanation
        st.subheader("🧠 Why This Prediction?")
        
        exp_col1, exp_col2 = st.columns([1, 1])
        
        with exp_col1:
            st.write("**🛣️ Route Information:**")
            st.write(f"• Length: {route_info['length']:.1f} km")
            st.write(f"• Base delay: {prediction['base_delay']} minutes")
            st.write(f"  (longer routes = more delays)")
            
            st.write("**🌤️ Weather Impact:**")
            st.write(f"• Today's weather: {prediction['weather']}")
            weather_impact = round((prediction['weather_factor'] - 1) * 100)
            if weather_impact > 0:
                st.write(f"• Adds {weather_impact}% more delay")
            else:
                st.write(f"• No weather delays today! 🎉")
        
        with exp_col2:
            st.write("**⏰ Time Impact:**")
            st.write(f"• Current period: {prediction['time_period']}")
            time_impact = round((prediction['time_factor'] - 1) * 100)
            if time_impact > 0:
                st.write(f"• Adds {time_impact}% more delay")
            else:
                st.write(f"• Good timing! No rush hour delays")
            
            st.write("**🎲 Random Factors:**")
            st.write("• Construction work")
            st.write("• Traffic accidents") 
            st.write("• Extra passengers")
            st.write("• Driver breaks")
        
        # Delay breakdown chart
        st.subheader("📊 Delay Breakdown")
        
        factors = {
            'Base Route Delay': prediction['base_delay'],
            'Weather Effect': prediction['base_delay'] * (prediction['weather_factor'] - 1),
            'Time Effect': prediction['base_delay'] * (prediction['time_factor'] - 1),
            'Random Factors': delay - prediction['base_delay'] * prediction['weather_factor'] * prediction['time_factor']
        }
        
        # Remove negative values
        factors = {k: max(0, v) for k, v in factors.items()}
        
        # Show chart
        if sum(factors.values()) > 0:
            st.bar_chart(factors)
        
        # Tips for users
        st.subheader("💡 Tips for Your Journey")
        
        if delay <= 2:
            st.success("✅ Great timing! Your bus should be on schedule.")
        elif delay <= 5:
            st.warning("⚠️ Minor delays possible. Consider leaving 5 minutes early.")
        elif delay <= 10:
            st.warning("⚠️ Moderate delays expected. Leave 10-15 minutes early.")
        else:
            st.error("🚨 Significant delays likely. Consider alternate routes or leave much earlier.")
        
        # Departure recommendation
        if delay > 2:
            st.info(f"💡 **Recommendation:** Leave {delay + 5} minutes earlier than usual to arrive on time!")

# Run the app
if __name__ == "__main__":
    main()
