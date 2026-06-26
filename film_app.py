import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Film Rental Business Dashboard", page_icon="🎬", layout="wide")

# Data Loading
@st.cache_data
def load_data():
    df = pd.read_csv("film_dataset.csv")
    df["rental_date"] = pd.to_datetime(df["rental_date"])
    df["payment_date"] = pd.to_datetime(df["payment_date"])
    df["rental_month"] = df["rental_date"].dt.to_period("M").astype(str)
    return df
#create sidebar
def create_sidebar_filters(df):
    st.sidebar.title("Dashboard Controls")
    
    # Page Navigation
    page = st.sidebar.radio(
        "Go to Page:",
        ["Executive Overview", "Customer Analytics", "Film & Category Performance", "Store & Staff Performance", "Geographic Insights"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")
    
    # Date Filter
    min_date = df["rental_date"].min().date()
    max_date = df["rental_date"].max().date()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
    
    # Category Filter
    categories = st.sidebar.multiselect(
        "Select Categories", 
        options=sorted(df["category"].unique()), 
        default=sorted(df["category"].unique()))
    
    # Store Filter
    stores = st.sidebar.multiselect(
        "Select Stores", 
        options=sorted(df["store_id"].unique()), 
        default=sorted(df["store_id"].unique()))
    
    # Country Filter
    countries = st.sidebar.multiselect(
        "Select Countries", 
        options=sorted(df["country"].unique()), 
        default=sorted(df["country"].unique()))
    
    return page, date_range, categories, stores, countries

#  Filter Application Logic
def filter_data(df, date_range, categories, stores, countries):
    filtered_df = df.copy()
    
    # Apply Date Range Filter
    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + pd.Timedelta(days=1)
        filtered_df = filtered_df[(filtered_df["rental_date"] >= start_date) & (filtered_df["rental_date"] < end_date)]
        
    # Apply Categorical Filters
    if categories:
        filtered_df = filtered_df[filtered_df["category"].isin(categories)]
    if stores:
        filtered_df = filtered_df[filtered_df["store_id"].isin(stores)]
    if countries:
        filtered_df = filtered_df[filtered_df["country"].isin(countries)]
        
    return filtered_df

#Page Rendering Functions

def render_executive_overview(df):
    st.title("📊 Executive Overview")
    
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    total_rev = df["payment_amount"].sum()
    total_rentals = df["rental_id"].nunique()
    active_cust = df["customer_id"].nunique()
    
    # Simple Month-over-Month calculation placeholder
    monthly_rev = df.groupby("rental_month")["payment_amount"].sum()
    mom_growth = ((monthly_rev.pct_change().iloc[-1] * 100)) if len(monthly_rev) > 1 else 0
    
    c1.metric("Total Revenue", f"${total_rev:,.2f}")
    c2.metric("Total Rentals", f"{total_rentals:,}")
    c3.metric("Active Customers", f"{active_cust:,}")
    c4.metric("Monthly Revenue Growth", f"{mom_growth:.1f}%" if len(monthly_rev) > 1 else 0)
    
    st.markdown("---")
    
    # Trend Chart
    st.subheader("📈 Monthly Revenue Trend")
    monthly_trend = df.groupby("rental_month").agg({"payment_amount": "sum", "rental_id": "count"}).reset_index()
    fig = px.line(monthly_trend, x="rental_month", y="payment_amount", labels={"payment_amount": "Revenue ($)", "rental_month": "Month"}, markers=True)
    st.plotly_chart(fig, use_container_width=True)

def render_customer_analytics(df):
    st.title("👥 Customer Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔝 Top 10 Customers by Revenue")
        top_cust = df.groupby("customer_name")["payment_amount"].sum().reset_index().sort_values(by="payment_amount", ascending=False).head(10)
        fig = px.bar(top_cust, x="payment_amount", y="customer_name", orientation="h", labels={"payment_amount": "Spent ($)", "customer_name": "Customer"})
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("🔄 Rental Frequency Retention Metrics")
        cust_rentals = df.groupby("customer_name")["rental_id"].count().reset_index()
        fig = px.histogram(cust_rentals, x="rental_id", nbins=20, labels={"rental_id": "Number of Rentals", "count": "Customer Count"})
        st.plotly_chart(fig, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Customer Churn & Risk Analysis")

    # Identify risk based on gap metric or lower total rentals

    cust_risk = df.groupby(["customer_name", "country"]).agg(
        total_spent=("payment_amount", "sum"),
        total_rentals=("rental_id", "count"),
        avg_gap=("gap", "mean")
    ).reset_index()
    
    # Add a custom flag rule based on standard gap metrics

    cust_risk["Risk Status"] = cust_risk["avg_gap"].apply(lambda x: "High Risk" if x > 5 else ("Medium Risk" if x > 2 else "Low Risk"))
    
    st.dataframe(cust_risk.sort_values("avg_gap", ascending=False), use_container_width=True)

def render_film_performance(df):
    st.title("🎬 Film & Category Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Most Rented Film Titles")
        top_films = df.groupby("film_title")["rental_id"].count().reset_index().sort_values(by="rental_id", ascending=False).head(10)
        fig = px.bar(top_films, x="rental_id", y="film_title", orientation="h", labels={"rental_id": "Rentals", "film_title": "Film Title"})
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("🍕 Revenue share by Category")
        cat_rev = df.groupby("category")["payment_amount"].sum().reset_index()
        fig = px.pie(cat_rev, values="payment_amount", names="category", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
    st.markdown("---")
    st.subheader("🚨 Inventory Stock Out / Rental Duration Risk")
    # Films keeping customers waiting too long based on actual duration vs baseline
    inventory_risk = df.groupby("film_title").agg(
        avg_rental_duration=("rental_duration", "mean"),
        total_rentals=("rental_id", "count")
    ).reset_index().sort_values(by="avg_rental_duration", ascending=False)
    
    st.dataframe(inventory_risk.head(100), use_container_width=True)

def render_store_performance(df):
    st.title("🏬 Store & Staff Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏪 Store Performance Comparison")
        store_comp = df.groupby("store_id").agg({"payment_amount": "sum", "rental_id": "count"}).reset_index()
        store_comp["store_id"] = store_comp["store_id"].astype(str)
        fig = px.bar(store_comp, x="store_id", y="payment_amount", color="store_id", labels={"payment_amount": "Total Revenue ($)", "store_id": "Store ID"})
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("👷 Staff Work Efficiency (Rentals Processed)")
        staff_comp = df.groupby("staff_name")["rental_id"].count().reset_index()
        fig = px.bar(staff_comp, x="staff_name", y="rental_id", color="staff_name", labels={"rental_id": "Rentals Handled", "staff_name": "Staff Member"})
        st.plotly_chart(fig, use_container_width=True)

def render_geographic_insights(df):
    st.title("🌍 Geographic Insights")
    
    st.subheader("🗺️ Revenue Distribution by Country")
    geo_country = df.groupby("country")["payment_amount"].sum().reset_index().sort_values(by="payment_amount", ascending=False)
    fig = px.bar(geo_country.head(15), x="country", y="payment_amount", text_auto='.2s', labels={"payment_amount": "Revenue ($)"})
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🎯 Regional Preferences (Top Categories per Country)")
    regional_pref = df.groupby(["country", "category"])["rental_id"].count().reset_index()

    # Filter for countries with relevant sample sizes

    top_countries = geo_country.head(5)["country"].tolist()
    regional_pref = regional_pref[regional_pref["country"].isin(top_countries)]
    
    fig2 = px.bar(regional_pref, x="country", y="rental_id", color="category", barmode="group", labels={"rental_id": "Rentals Count"})
    st.plotly_chart(fig2, use_container_width=True)

def main():
    # Load dataset
    raw_df = load_data()
    
    # Generate sidebar filters
    page, date_range, categories, stores, countries = create_sidebar_filters(raw_df)
    
    # Filter data dynamically
    filtered_df = filter_data(raw_df, date_range, categories, stores, countries)
    
    # Check if filters returned empty data
    if filtered_df.empty:
        st.warning("⚠️ No data matches the current filters. Please broaden your selection.")
        return

    # Route to selected page
    if page == "Executive Overview":
        render_executive_overview(filtered_df)
    elif page == "Customer Analytics":
        render_customer_analytics(filtered_df)
    elif page == "Film & Category Performance":
        render_film_performance(filtered_df)
    elif page == "Store & Staff Performance":
        render_store_performance(filtered_df)
    elif page == "Geographic Insights":
        render_geographic_insights(filtered_df)
        
    # Global Download feature at the bottom
    st.markdown("---")
    st.subheader("💾 Export Filtered Dataset")
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv_data,
        file_name="filtered_film_data.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()