import streamlit as st
import numpy as np
import pickle
import pandas as pd

# ─── Page Configuration (MUST BE FIRST!) ───
st.set_page_config(
    page_title="Kenya House Price Predictor",
    page_icon="🏠",
    layout="centered"
)

from database import (init_db, save_prediction, get_user_predictions,
                      get_user_stats, get_all_users, get_all_predictions,
                      get_overall_stats, delete_user)
from auth import is_logged_in, logout, show_auth_page, is_admin

# ─── Initialize Database ───
init_db()

# ─── Load Model & Scaler ───
@st.cache_resource
def load_model():
    with open('best_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    return model, scaler

model, scaler = load_model()

# ─── Mappings ───
location_mapping = {
    'Kabete': 0, 'Karen': 1, 'Kiambu Road': 2, 'Kileleshwa': 3,
    'Kilimani': 4, 'Kitisuru': 5, 'Kyuna': 6, 'Lavington': 7,
    'Loresho': 8, 'Lower Kabete': 9, 'Muthaiga': 10, 'Muthaiga North': 11,
    'Nairobi West': 12, 'Ngong Rd': 13, 'Nyari': 14, 'Ongata Rongai': 15,
    'Parklands': 16, 'Riverside': 17, 'Rosslyn': 18, 'Runda': 19,
    'Syokimau': 20, 'Thigiri': 21, 'Thome': 22, 'Waithaka': 23,
    'Westlands': 24
}

property_mapping = {
    'Apartment': 0,
    'Townhouse': 1,
    'Vacant Land': 2
}

# ─── Show Login if Not Logged In ───
if not is_logged_in():
    show_auth_page()
    st.stop()

# ─── Sidebar ───
with st.sidebar:
    st.markdown(f"""
        <div style='text-align: center; padding: 10px;'>
            <h2>👤 {st.session_state.user['username']}</h2>
            <p style='color: #666;'>{'🔴 Admin' if is_admin() else '🟢 User'}</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    if is_admin():
        page = st.radio("Navigate", [
            "👨‍💼 Admin Dashboard",
            "👥 All Users",
            "📊 All Predictions",
        ])
    else:
        page = st.radio("Navigate", [
            "🏠 Predict Price",
            "📊 My History",
            "📈 My Stats"
        ])

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        logout()

# ════════════════════════════════════════
# USER PAGES
# ════════════════════════════════════════

# ─── Page: Predict Price ───
if not is_admin() and page == "🏠 Predict Price":

    st.markdown("""
        <h1 style='text-align: center; color: #1A365D;'>
            🏠 Kenya House Price Predictor
        </h1>
        <p style='text-align: center; color: #666;'>
            Enter property details to get an estimated market price
        </p>
        <hr>
    """, unsafe_allow_html=True)

    st.markdown("### 📋 Property Details")

    col1, col2 = st.columns(2)

    with col1:
        location = st.selectbox(
            "📍 Location",
            options=list(location_mapping.keys())
        )
        property_type = st.selectbox(
            "🏗️ Property Type",
            options=list(property_mapping.keys())
        )
        bedrooms = st.slider(
            "🛏️ Number of Bedrooms",
            min_value=1, max_value=8, value=3
        )

    with col2:
        bathrooms = st.slider(
            "🚿 Number of Bathrooms",
            min_value=1, max_value=8, value=2
        )
        land_size = st.number_input(
            "🌍 Land Size (acres)",
            min_value=0.1, max_value=10.0,
            value=0.5, step=0.1
        )
        house_size = st.number_input(
            "📐 House Size (m²)",
            min_value=10.0, max_value=2000.0,
            value=150.0, step=10.0
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔍 Predict House Price", use_container_width=True):

        location_encoded = location_mapping[location]
        property_encoded = property_mapping[property_type]

        input_data = np.array([[
            bedrooms, bathrooms, land_size,
            property_encoded, location_encoded
        ]])

        input_scaled    = scaler.transform(input_data)
        log_price       = model.predict(input_scaled)[0]
        predicted_price = float(np.exp(log_price))

        # Save to database
        save_prediction(
            user_id         = st.session_state.user['id'],
            location        = location,
            property_type   = property_type,
            bedrooms        = bedrooms,
            bathrooms       = bathrooms,
            land_size       = land_size,
            house_size      = house_size,
            predicted_price = predicted_price
        )

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 💰 Prediction Result")

        formatted_price = f"KSh {predicted_price:,.0f}"

        if predicted_price < 10_000_000:
            color = "#276749"
            label = "Affordable Range"
        elif predicted_price < 50_000_000:
            color = "#2B6CB0"
            label = "Mid Range"
        elif predicted_price < 150_000_000:
            color = "#C05621"
            label = "High End"
        else:
            color = "#822727"
            label = "Luxury Property"

        st.markdown(f"""
            <div style='
                background-color: {color};
                padding: 30px;
                border-radius: 12px;
                text-align: center;
            '>
                <p style='color: white; font-size: 16px;'>{label}</p>
                <h1 style='color: white; font-size: 42px;'>{formatted_price}</h1>
                <p style='color: rgba(255,255,255,0.8); font-size: 13px;'>
                    Estimated Market Value
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("📍 Location", location)
        c2.metric("🏗️ Type", property_type)
        c3.metric("🛏️ Bedrooms", bedrooms)

        c4, c5, c6 = st.columns(3)
        c4.metric("🚿 Bathrooms", bathrooms)
        c5.metric("🌍 Land Size", f"{land_size} acres")
        c6.metric("📐 House Size", f"{house_size} m²")

        low  = predicted_price * 0.85
        high = predicted_price * 1.15
        st.info(f"""
            Estimated range: **KSh {low:,.0f}** — **KSh {high:,.0f}** *(±15%)*
        """)
        st.success("✅ Prediction saved to your history!")

# ─── Page: My History ───
elif not is_admin() and page == "📊 My History":
    st.markdown("## 📊 My Prediction History")
    st.markdown("<hr>", unsafe_allow_html=True)

    predictions = get_user_predictions(st.session_state.user['id'])

    if not predictions:
        st.info("No predictions yet! Go to 🏠 Predict Price to get started.")
    else:
        st.markdown(f"**Total predictions: {len(predictions)}**")
        st.markdown("<br>", unsafe_allow_html=True)

        for pred in predictions:
            location, prop_type, beds, baths, land, house, price, date = pred
            price = float(price)
            with st.expander(
                f"🏠 {location} — KSh {price:,.0f}  |  {str(date)[:10]}"
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("📍 Location", location)
                c2.metric("🏗️ Type", prop_type)
                c3.metric("💰 Price", f"KSh {price:,.0f}")

                c4, c5, c6 = st.columns(3)
                c4.metric("🛏️ Bedrooms", beds)
                c5.metric("🚿 Bathrooms", baths)
                c6.metric("🌍 Land", f"{land} acres")

# ─── Page: My Stats ───
elif not is_admin() and page == "📈 My Stats":
    st.markdown("## 📈 My Statistics")
    st.markdown("<hr>", unsafe_allow_html=True)

    total, avg, maximum, minimum = get_user_stats(st.session_state.user['id'])

    if total == 0:
        st.info("No predictions yet! Make some predictions first.")
    else:
        c1, c2 = st.columns(2)
        c1.metric("🔢 Total Predictions", total)
        c2.metric("📊 Average Price", f"KSh {avg:,.0f}" if avg else "N/A")

        c3, c4 = st.columns(2)
        c3.metric("⬆️ Highest", f"KSh {maximum:,.0f}" if maximum else "N/A")
        c4.metric("⬇️ Lowest", f"KSh {minimum:,.0f}" if minimum else "N/A")

        predictions = get_user_predictions(st.session_state.user['id'])
        if predictions:
            df_hist = pd.DataFrame(predictions, columns=[
                'Location', 'Type', 'Bedrooms', 'Bathrooms',
                'Land Size', 'House Size', 'Price', 'Date'
            ])
            df_hist['Price'] = df_hist['Price'].astype(float)
            df_hist['Date']  = pd.to_datetime(df_hist['Date'])
            df_hist = df_hist.sort_values('Date')

            st.markdown("### 💰 Price Trend")
            st.line_chart(df_hist.set_index('Date')['Price'])

            st.markdown("### 📍 Predictions by Location")
            st.bar_chart(df_hist['Location'].value_counts())

# ════════════════════════════════════════
# ADMIN PAGES
# ════════════════════════════════════════

# ─── Admin: Dashboard ───
elif is_admin() and page == "👨‍💼 Admin Dashboard":
    st.markdown("## 👨‍💼 Admin Dashboard")
    st.markdown("<hr>", unsafe_allow_html=True)

    stats = get_overall_stats()

    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Total Users",       stats['total_users'])
    c2.metric("🔢 Total Predictions", stats['total_predictions'])
    c3.metric("📊 Avg Price",
              f"KSh {stats['avg_price']:,.0f}" if stats['avg_price'] else "N/A")

    c4, c5 = st.columns(2)
    c4.metric("⬆️ Highest",
              f"KSh {stats['max_price']:,.0f}" if stats['max_price'] else "N/A")
    c5.metric("⬇️ Lowest",
              f"KSh {stats['min_price']:,.0f}" if stats['min_price'] else "N/A")

    all_preds = get_all_predictions()
    if all_preds:
        st.markdown("<br>", unsafe_allow_html=True)
        df_admin = pd.DataFrame(all_preds, columns=[
            'User', 'Location', 'Type', 'Bedrooms',
            'Bathrooms', 'Land Size', 'House Size', 'Price', 'Date'
        ])
        df_admin['Price'] = df_admin['Price'].astype(float)

        st.markdown("### 📍 Most Searched Locations")
        st.bar_chart(df_admin['Location'].value_counts())

        st.markdown("### 🏗️ Most Searched Property Types")
        st.bar_chart(df_admin['Type'].value_counts())
    else:
        st.info("No predictions made yet by any user.")

# ─── Admin: All Users ───
elif is_admin() and page == "👥 All Users":
    st.markdown("## 👥 All Registered Users")
    st.markdown("<hr>", unsafe_allow_html=True)

    users = get_all_users()

    if not users:
        st.info("No users registered yet!")
    else:
        st.markdown(f"**Total Users: {len(users)}**")
        df_users = pd.DataFrame(users, columns=[
            'ID', 'Username', 'Email', 'Registered At'
        ])
        st.dataframe(df_users, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🗑️ Delete a User")
        st.warning("⚠️ Deleting a user also deletes all their predictions!")

        user_options = [f"{u[0]} — {u[1]}" for u in users]
        user_to_delete = st.selectbox("Select user to delete", options=user_options)

        if st.button("🗑️ Delete User", type="primary"):
            user_id = int(user_to_delete.split(" — ")[0])
            delete_user(user_id)
            st.success("✅ User deleted successfully!")
            st.rerun()

# ─── Admin: All Predictions ───
elif is_admin() and page == "📊 All Predictions":
    st.markdown("## 📊 All Predictions")
    st.markdown("<hr>", unsafe_allow_html=True)

    all_preds = get_all_predictions()

    if not all_preds:
        st.info("No predictions made yet!")
    else:
        df_preds = pd.DataFrame(all_preds, columns=[
            'User', 'Location', 'Type', 'Bedrooms',
            'Bathrooms', 'Land Size', 'House Size', 'Price', 'Date'
        ])
        df_preds['Price'] = df_preds['Price'].astype(float)
        st.markdown(f"**Total Predictions: {len(df_preds)}**")
        df_preds['Price'] = df_preds['Price'].apply(lambda x: f"KSh {x:,.0f}")
        st.dataframe(df_preds, use_container_width=True)

# ─── Footer ───
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
    <p style='text-align: center; color: #999; font-size: 13px;'>
        🏠 Kenya House Price Predictor | Built with Machine Learning & Streamlit
    </p>
""", unsafe_allow_html=True)