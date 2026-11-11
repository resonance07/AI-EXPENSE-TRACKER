import re
import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# File path for CSV database
DATA_FILE = "expenses.csv"

# Predefined categories and keyword rules
CATEGORY_RULES = {
    "Food & Dining": ["dinner", "lunch", "breakfast", "coffee", "zomato", "swiggy", "groceries", "restaurant", "food", "snacks"],
    "Transportation": ["uber", "ola", "metro", "cab", "petrol", "diesel", "auto", "bus", "train", "flight", "fuel"],
    "Shopping": ["clothes", "shoes", "amazon", "flipkart", "electronics", "shopping", "mall"],
    "Bills & Utilities": ["recharge", "wifi", "electricity", "rent", "water", "bill", "subscription", "netflix"],
    "Entertainment": ["movie", "cinema", "concert", "game", "outing", "party"]
}

# --- Data Helpers ---
def load_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(DATA_FILE)
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Date", "Amount", "Category", "Description"])
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df: pd.DataFrame):
    df.to_csv(DATA_FILE, index=False)

def parse_expense(text: str):
    """Extracts Amount, Category, and Description from natural language input."""
    amount_match = re.search(r'(?:(?:rs\.?|₹|\$)\s*)?(\d+(?:\.\d{1,2})?)', text, re.IGNORECASE)
    if not amount_match:
        return None
    
    amount = float(amount_match.group(1))
    text_lower = text.lower()
    category = "Other"
    
    for cat, keywords in CATEGORY_RULES.items():
        if any(keyword in text_lower for keyword in keywords):
            category = cat
            break

    return {
        "Date": datetime.date.today().strftime("%Y-%m-%d"),
        "Amount": amount,
        "Category": category,
        "Description": text.strip()
    }

# --- Streamlit UI Setup ---
st.set_page_config(
    page_title="AI Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("💰 AI Expense Tracker Dashboard")
st.caption("Log expenses naturally and track your spending insights visually.")

df = load_data()

# --- Sidebar: Add New Expense ---
st.sidebar.header("➕ Quick Expense Logger")

# Natural Language Logger
st.sidebar.subheader("AI Natural Language Input")
nl_input = st.sidebar.text_input("Log expense:", placeholder="e.g., Spent 450 on dinner with friends")

if st.sidebar.button("Parse & Log Expense", type="primary"):
    if nl_input:
        parsed = parse_expense(nl_input)
        if parsed:
            new_row = pd.DataFrame([parsed])
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.sidebar.success(f"Added: ₹{parsed['Amount']} → [{parsed['Category']}]")
            st.rerun()
        else:
            st.sidebar.error("Could not detect a valid numeric amount.")
    else:
        st.sidebar.warning("Please enter an expense string.")

st.sidebar.markdown("---")

# Manual Entry Form
with st.sidebar.expander("Manual Entry Form"):
    with st.form("manual_form", clear_on_submit=True):
        m_date = st.date_input("Date", datetime.date.today())
        m_amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
        m_category = st.selectbox("Category", list(CATEGORY_RULES.keys()) + ["Other"])
        m_desc = st.text_input("Description")
        
        if st.form_submit_button("Add Entry"):
            if m_amount > 0:
                new_entry = {
                    "Date": m_date.strftime("%Y-%m-%d"),
                    "Amount": m_amount,
                    "Category": m_category,
                    "Description": m_desc if m_desc else m_category
                }
                df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                save_data(df)
                st.success("Entry added manually!")
                st.rerun()

# --- Main Dashboard ---
if df.empty:
    st.info("No expenses logged yet. Use the sidebar to log your first expense!")
else:
    # Key Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    total_spent = df["Amount"].sum()
    avg_expense = df["Amount"].mean()
    total_transactions = len(df)
    top_category = df.groupby("Category")["Amount"].sum().idxmax()

    col1.metric("Total Spent", f"₹{total_spent:,.2f}")
    col2.metric("Average Transaction", f"₹{avg_expense:,.2f}")
    col3.metric("Total Transactions", total_transactions)
    col4.metric("Top Spending Category", top_category)

    st.markdown("---")

    # Interactive Visualizations
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Spending by Category")
        cat_summary = df.groupby("Category")["Amount"].sum().reset_index()
        fig_pie = px.pie(
            cat_summary, 
            values="Amount", 
            names="Category", 
            hole=0.4, 
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        st.subheader("Daily Spending Trend")
        daily_summary = df.groupby("Date")["Amount"].sum().reset_index()
        fig_line = px.line(
            daily_summary, 
            x="Date", 
            y="Amount", 
            markers=True,
            line_shape="spline",
            color_discrete_sequence=["#2E86C1"]
        )
        fig_line.update_layout(xaxis_title="Date", yaxis_title="Amount (₹)")
        st.plotly_chart(fig_line, use_container_width=True)

    # Filterable Data Table
    st.markdown("---")
    st.subheader("📋 Expense History & Management")

    filter_cat = st.multiselect("Filter by Category", options=df["Category"].unique(), default=df["Category"].unique())
    filtered_df = df[df["Category"].isin(filter_cat)]

    st.dataframe(
        filtered_df.sort_values(by="Date", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # Clear Data Option
    if st.button("⚠️ Clear All Data"):
        pd.DataFrame(columns=["Date", "Amount", "Category", "Description"]).to_csv(DATA_FILE, index=False)
        st.rerun()
