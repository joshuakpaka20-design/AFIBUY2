
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from sklearn.linear_model import LinearRegression
import numpy as np
import hashlib

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Afibuy Trade Intelligence",
    layout="wide"
)

# ---------------- CUSTOM STYLING ----------------
st.markdown(
    """
    <style>

    .main {
        background-color: #0E1117;
        color: white;
    }

    .stApp {
        background-color: #0E1117;
    }

    section[data-testid="stSidebar"] {
        background-color: #111827;
    }

    h1, h2, h3, h4 {
        color: #00D4FF;
    }

    .stMetric {
        background-color: #1F2937;
        padding: 15px;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ==================================================
# USER AUTHENTICATION SYSTEM
# ==================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# Establish database connection (or create if not exists)
conn = sqlite3.connect("afibuy_database.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")
conn.commit()

# Login/Register UI on sidebar
auth_mode = st.sidebar.selectbox(
    "Account",
    ["Login", "Register"]
)

if not st.session_state.logged_in:

    st.title("🔐 Afibuy Authentication")

    username_input = st.text_input("Username")

    password_input = st.text_input(
        "Password",
        type="password"
    )

    # ==================================================
    # REGISTER
    # ==================================================

    if auth_mode == "Register":

        if st.button("Create Account"):
            hashed_password = hashlib.sha256(password_input.encode()).hexdigest()
            try:

                cursor.execute(
                    """
                    INSERT INTO users (
                        username,
                        password
                    )
                    VALUES (?, ?)
                    """,
                    (
                        username_input,
                        hashed_password
                    )
                )

                conn.commit()

                st.success(
                    "Account created successfully!"
                )

            except sqlite3.IntegrityError:

                st.error(
                    "Username already exists."
                )

    # ==================================================
    # LOGIN
    # ==================================================

    elif auth_mode == "Login":

        if st.button("Login"):
            hashed_password = hashlib.sha256(password_input.encode()).hexdigest()

            cursor.execute(
                """
                SELECT * FROM users
                WHERE username = ?
                AND password = ?
                """,
                (
                    username_input,
                    hashed_password
                )
            )

            user = cursor.fetchone()

            if user:

                st.session_state.logged_in = True

                st.session_state.username = (
                    username_input
                )

                st.success(
                    "Login successful!"
                )

            else:

                st.error(
                    "Invalid username or password"
                )

    st.stop()

# ---------------- LOGOUT SYSTEM ----------------
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Logged out successfully!")
    st.stop()

st.success(
    f"Welcome, {st.session_state.username}"
)

# ---------------- LOAD DATA FROM DATABASE ----------------
query = "SELECT * FROM trade_data"
df = pd.read_sql(query, conn)

# ---------------- RISK ANALYSIS (GLOBAL) ----------------
def calculate_risk(margin):

    if margin >= 40:
        return "Low Risk"

    elif margin >= 20:
        return "Medium Risk"

    else:
        return "High Risk"

df["Risk_Level"] = df["Profit_Margin_%"] # Original error: df["Profit_Margin_%"] needs .apply(calculate_risk) here. Fixed below.
df["Risk_Level"] = df["Profit_Margin_%"].apply(calculate_risk)

# ---------------- OPPORTUNITY SCORE ----------------

def calculate_score(row):

    score = 0

    # Profit Margin Score
    if row["Profit_Margin_%"] >= 40:
        score += 50

    elif row["Profit_Margin_%"] >= 20:
        score += 30

    else:
        score += 10

    # Profit Score
    if row["Profit_USD"] >= 1000:
        score += 30

    else:
        score += 15

    # Risk Score
    if row["Risk_Level"] == "Low Risk":
        score += 20

    elif row["Risk_Level"] == "Medium Risk":
        score += 10

    return score

df["Opportunity_Score"] = df.apply(
    calculate_score,
    axis=1
)

# ==================================================
# MACHINE LEARNING PROFIT FORECASTING
# ==================================================

# Features and target
X = df[["Import_Cost_USD"]]
y = df["Selling_Price_USD"]

# Train model
model = LinearRegression()

model.fit(X, y)

# Predict future selling prices
df["Predicted_Selling_Price"] = model.predict(X)

# Predict future profit
df["Predicted_Profit"] = (
    df["Predicted_Selling_Price"] -
    df["Import_Cost_USD"]
).round(2)

# ---------------- LIVE EXCHANGE RATES ----------------
exchange_rates = {
    "USD_TO_MAD": 9.85,
    "USD_TO_LRD": 198.50,
    "USD_TO_NGN": 1520.00,
    "USD_TO_GHS": 15.20,
    "USD_TO_XOF": 605.00
}

# ---------------- SIDEBAR BRANDING ----------------
st.sidebar.title("🌍 Afibuy")
st.sidebar.markdown("""
### Trade Intelligence Platform

Helping African traders make smarter decisions using:

- Market analytics
- Price intelligence
- Profit forecasting
- Trade insights
""")

st.sidebar.markdown("# ---------------- LIVE FX PANEL ----------------")
st.sidebar.subheader("💱 Live Exchange Rates")
st.sidebar.metric("USD → MAD", exchange_rates["USD_TO_MAD"])
st.sidebar.metric("USD → LRD", exchange_rates["USD_TO_LRD"])
st.sidebar.metric("USD → NGN", exchange_rates["USD_TO_NGN"])
st.sidebar.metric("USD → GHS", exchange_rates["USD_TO_GHS"])
st.sidebar.metric("USD → XOF", exchange_rates["USD_TO_XOF"])

# ---------------- SIDEBAR NAVIGATION ----------------
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "Trade Calculator",
        "Price Explorer",
        "Market Insights",
        "Admin Analytics"
    ]
)

# ---------------- TITLE ----------------
st.title("🌍 Afibuy Trade Intelligence Platform")
st.markdown("""
### African Cross-Border Market Intelligence System
""")

# ==================================================
# DASHBOARD
# ==================================================

if menu == "Dashboard":

    st.header("📊 Trade Opportunities Dashboard")

    # Filters
    country_filter = st.sidebar.multiselect(
        "Select Destination Country",
        options=df["Destination_Country"].unique(),
        default=df["Destination_Country"].unique()
    )

    product_filter = st.sidebar.multiselect(
        "Select Product",
        options=df["Product"].unique(),
        default=df["Product"].unique()
    )

    filtered_df = df[
        (df["Destination_Country"].isin(country_filter)) &
        (df["Product"].isin(product_filter))
    ]

    total_products = len(filtered_df)
    total_profit = filtered_df["Profit_USD"].sum()

    # Correct calculation for average margin
    avg_margin = 0.0 # Default value if no data
    if not filtered_df.empty: # Check if filtered_df is not empty before calling .mean()
        avg_margin = filtered_df["Profit_Margin_%"].mean()

    # Initial KPI cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Products", total_products)
    col2.metric("Total Profit (USD)", f"${total_profit:.2f}") # Format to 2 decimal places
    col3.metric("Average Margin", f"{avg_margin:.2f}%")

    # ---------------- TOP INSIGHTS ----------------

    if not filtered_df.empty:
        top_trade = filtered_df.loc[
            filtered_df["Profit_USD"].idxmax()
        ]

        st.subheader("🏆 Top Trade Opportunity")

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "Best Product",
            top_trade["Product"]
        )

        col5.metric(
            "Highest Profit",
            f"${top_trade['Profit_USD']:.2f}"
        )

        col6.metric(
            "Top Route",
            f"{top_trade['Source_Country']} → {top_trade['Destination_Country']}"
        )

        st.success(
            f"""
        Best current opportunity is importing
        {top_trade['Product']}
        from {top_trade['Source_Country']}
        into
        {top_trade['Destination_Country']}.
        """
        )
    else:
        st.info("No data available for the selected filters to determine top trade opportunity.")

    # Additional KPI card for Countries Covered
    col7_container = st.columns(1)[0]
    col7_container.metric(
        "Countries Covered",
        filtered_df["Destination_Country"].nunique()
    )


    st.subheader("Trade Dataset")
    st.dataframe(filtered_df)

    # ---------------- TOP OPPORTUNITIES ----------------

    st.subheader("🚀 Top Trade Opportunities")

    if not filtered_df.empty:
        top_opportunities = filtered_df.sort_values(
            by="Opportunity_Score",
            ascending=False
        )

        st.dataframe(
            top_opportunities[
                [
                    "Product",
                    "Source_Country",
                    "Destination_Country",
                    "Profit_USD",
                    "Profit_Margin_%",
                    "Risk_Level",
                    "Opportunity_Score"
                ]
            ]
        )
    else:
        st.info("No data available for top trade opportunities with current filters.")

    st.subheader("Profit by Product")

    fig = px.bar(
        filtered_df,
        x="Product",
        y="Profit_USD",
        color="Product",
        title="Profitability by Product"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------- RISK ANALYSIS SUMMARY ----------------
    st.subheader("⚠️ Risk Analysis Summary")

    if not filtered_df.empty:
        risk_counts = filtered_df["Risk_Level"].value_counts().reset_index()
        risk_counts.columns = ['Risk Level', 'Number of Trades']
        st.dataframe(risk_counts)

        # ---------------- RISK VISUALIZATION ----------------
        st.subheader("📊 Trade Risk Distribution")

        risk_fig = px.pie(
            filtered_df,
            names="Risk_Level",
            title="Trade Risk Levels"
        )

        st.plotly_chart(
            risk_fig,
            use_container_width=True
        )
    else:
        st.info("No data available for risk analysis with current filters.")

    # ---------------- EXPORT DATA ----------------
    st.subheader("Download Trade Data")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Trade Report CSV",
        data=csv,
        file_name='afibuy_filtered_trade_report.csv',
        mime='text/csv',
    )


# ==================================================
# TRADE CALCULATOR
# ==================================================

elif menu == "Trade Calculator":

    st.header("💰 Trade Profit Calculator")

    product = st.text_input("Product Name")

    import_cost = st.number_input(
        "Import Cost (USD)",
        min_value=0.0
    )

    selling_price = st.number_input(
        "Selling Price (USD)",
        min_value=0.0
    )

    shipping_cost = st.number_input(
        "Shipping Cost (USD)",
        min_value=0.0
    )

    tax_cost = st.number_input(
        "Tax/Customs Cost (USD)",
        min_value=0.0
    )

    if st.button("Calculate Profit"):

        total_cost = (
            import_cost +
            shipping_cost +
            tax_cost
        )

        profit = selling_price - total_cost

        if total_cost > 0:
            margin = (profit / total_cost) * 100
        else:
            margin = 0

        st.success(f"Estimated Profit: ${profit:.2f}")

        st.info(f"Profit Margin: {margin:.2f}%")

        # ---------------- CURRENCY CONVERSION ----------------
        # Exchange rates (fictitious for demonstration)
        usd_to_mad = exchange_rates["USD_TO_MAD"]
        usd_to_lrd = exchange_rates["USD_TO_LRD"]
        usd_to_ngn = exchange_rates["USD_TO_NGN"]

        profit_mad = profit * usd_to_mad
        profit_lrd = profit * usd_to_lrd
        profit_ngn = profit * usd_to_ngn

        st.subheader("🌍 Multi-Currency Profit Estimates")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Profit in MAD",
            f"{profit_mad:.2f} MAD"
        )

        col2.metric(
            "Profit in LRD",
            f"{profit_lrd:.2f} LRD"
        )

        col3.metric(
            "Profit in NGN",
            f"{profit_ngn:.2f} NGN"
        )

# ==================================================
# PRICE EXPLORER
# ==================================================

elif menu == "Price Explorer":

    st.header("📈 Product Price Comparison")

    product_choice = st.selectbox(
        "Select Product",
        df["Product"].unique()
    )

    filtered_df = df[df["Product"] == product_choice]

    st.dataframe(filtered_df)

    fig = px.pie(
        filtered_df,
        names="Source_Country",
        values="Import_Cost_USD",
        title="Import Cost Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------- EXPORT DATA ----------------
    st.subheader("Download Price Data")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Price Report CSV",
        data=csv,
        file_name='afibuy_price_report.csv',
        mime='text/csv',
    )

# ==================================================
# MARKET INSIGHTS
# ==================================================

elif menu == "Market Insights":

    st.header("🌍 African Market Insights")

    highest_profit = df.loc[
        df["Profit_USD"].idxmax()
    ]

    st.success(
        f"Highest profit product: "
        f"{highest_profit['Product']}"
    )

    st.write(
        f"Profit: ${highest_profit['Profit_USD']:.2f}"
    )

    st.write(
        f"Trade Route: "
        f"{highest_profit['Source_Country']} → "
        f"{highest_profit['Destination_Country']}"
    )

    st.subheader("Average Profit Margin")

    fig = px.line(
        df,
        x="Product",
        y="Profit_Margin_%",
        markers=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==================================================
    # AI TRADE RECOMMENDATIONS
    # ==================================================

    st.subheader("🤖 AI Trade Recommendations")

    # Using 'df' as 'filtered_df' is not defined in this scope without explicit filters for Market Insights
    high_margin_df = df[
        df["Profit_Margin_%"] > 30
    ]

    if len(high_margin_df) > 0:

        for index, row in high_margin_df.iterrows():

            st.success(
                f"""
                AI Recommendation:
                Import {row['Product']}
                from {row['Source_Country']}
                and sell in
                {row['Destination_Country']}.

                Estimated Profit Margin:
                {row['Profit_Margin_%']}%"""
            )

    else:

        st.warning(
            "No high-margin trade opportunities found."
        )

    # ==================================================
    # AI FORECASTING DASHBOARD
    # ==================================================

    st.subheader("🤖 AI Profit Forecasting")

    forecast_df = df[
        [
            "Product",
            "Import_Cost_USD",
            "Selling_Price_USD",
            "Predicted_Selling_Price",
            "Predicted_Profit"
        ]
    ]

    st.dataframe(forecast_df)

    forecast_fig = px.bar(
        forecast_df,
        x="Product",
        y="Predicted_Profit",
        color="Product",
        title="Predicted Future Profit"
    )

    st.plotly_chart(
        forecast_fig,
        use_container_width=True
    )

# ==================================================
# ADMIN ANALYTICS PANEL
# ==================================================

elif menu == "Admin Analytics":

    st.header("📊 Executive Admin Analytics")

    total_transactions = len(df) * 125

    estimated_platform_revenue = (
        df["Profit_USD"].sum() * 0.02
    )

    active_trade_routes = len(
        df[
            [
                "Source_Country",
                "Destination_Country"
            ]
        ].drop_duplicates()
    )

    active_users = 2450

    col1, col2 = st.columns(2)

    col3, col4 = st.columns(2)

    col1.metric(
        "Estimated Transactions",
        total_transactions
    )

    col2.metric(
        "Platform Revenue",
        f"${estimated_platform_revenue:.2f}"
    )

    col3.metric(
        "Active Trade Routes",
        active_trade_routes
    )

    col4.metric(
        "Active Users",
        active_users
    )

    st.subheader("🌍 Revenue by Product")

    revenue_df = df.groupby(
        "Product"
    )["Profit_USD"].sum().reset_index()

    revenue_fig = px.bar(
        revenue_df,
        x="Product",
        y="Profit_USD",
        color="Product",
        title="Revenue Distribution"
    )

    st.plotly_chart(
        revenue_fig,
        use_container_width=True
    )

    st.subheader("📈 Platform Performance")

    performance_data = pd.DataFrame({
        "Month": [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun"
        ],

        "Users": [
            200,
            450,
            700,
            1200,
            1800,
            2450
        ]
    })

    performance_fig = px.line(
        performance_data,
        x="Month",
        y="Users",
        markers=True,
        title="Platform Growth"
    )

    st.plotly_chart(
        performance_fig,
        use_container_width=True
    )

    st.success(
        "Platform operating normally across African markets."
    )