import streamlit as st
import pg8000
import pandas as pd
import plotly.express as px
import os

# Secure database connection
def create_connection():
    connection = pg8000.connect(
        host=os.getenv("DB_HOST", "orders.ch2k6ywge94l.ap-south-1.rds.amazonaws.com"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "asdf1234567890"),
        port=os.getenv("DB_PORT", "5432")
    )
    return connection

# Function to execute queries
def run_query(query):
    connection = create_connection()
    if connection is None:
        return None
    try:
        df = pd.read_sql_query(query, connection)
        return df
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return None
    finally:
        connection.close()

# Streamlit app for SQL queries
def main():
    # Sidebar setup
    st.sidebar.title("Retail Order Data Analysis")
    
    guvi_queries = {
        "Top 10 highest revenue generating products": 
            'SELECT sub_category, SUM(sale_price * quantity) AS total_revenue FROM orders GROUP BY sub_category ORDER BY total_revenue DESC LIMIT 10;',
        "Top 5 cities with the highest profit margins": 
            'SELECT city, SUM((sale_price - cost_price) / sale_price) * 100 AS total_profit FROM orders WHERE sale_price > 0 GROUP BY city ORDER BY total_profit DESC LIMIT 5;',
        # Add more queries as needed
    }

    my_queries = {
        "1. Top 5 Products with the Highest Quantity of Orders": 
            'SELECT product_id, COUNT(order_id) AS total_orders FROM orders GROUP BY product_id ORDER BY total_orders DESC LIMIT 5;',
        "2. Total Revenue by Region": 
            'SELECT region, SUM(sale_price) AS total_revenue FROM orders GROUP BY region ORDER BY total_revenue DESC;',
        # Add more queries as needed
    }

    # Navigation for query selection
    nav = st.sidebar.radio("Select Query Section", ["Guvi Queries", "My Queries"])
    if nav == "Guvi Queries":
        st.subheader("Guvi Queries")
        query = st.selectbox("Select a query to visualize:", list(guvi_queries.keys()))
        selected_query_set = guvi_queries
    elif nav == "My Queries":
        st.subheader("My Queries")
        query = st.selectbox("Select a query to visualize:", list(my_queries.keys()))
        selected_query_set = my_queries
    else:
        query = None

    # Execute selected query
    if query:
        with st.spinner("Running query..."):
            result_df = run_query(selected_query_set[query])
        
        if result_df is not None and not result_df.empty:
            st.success("Query executed successfully!")
            st.dataframe(result_df)
            
            # CSV download button
            csv = result_df.to_csv(index=False)
            st.download_button("Download CSV", csv, "query_results.csv", "text/csv")
            
            # Visualization
            st.subheader("Visualization")
            chart_type = st.selectbox("Select Chart Type", ["None", "Bar Chart", "Line Chart", "Pie Chart"])
            
            if chart_type == "Bar Chart":
                x_axis = st.selectbox("Select X-axis", result_df.columns)
                y_axis = st.selectbox("Select Y-axis", result_df.columns)
                fig = px.bar(result_df, x=x_axis, y=y_axis)
                st.plotly_chart(fig)
            elif chart_type == "Line Chart":
                x_axis = st.selectbox("Select X-axis", result_df.columns)
                y_axis = st.selectbox("Select Y-axis", result_df.columns)
                fig = px.line(result_df, x=x_axis, y=y_axis)
                st.plotly_chart(fig)
            elif chart_type == "Pie Chart":
                names = st.selectbox("Select Names", result_df.columns)
                values = st.selectbox("Select Values", result_df.columns)
                fig = px.pie(result_df, names=names, values=values)
                st.plotly_chart(fig)
        else:
            st.warning("No results found for the selected query.")

# Run the app
if __name__ == "__main__":
    st.set_page_config(page_title="Retail Order Data Analysis", layout="wide")
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f5f5f5;
            font-family: 'Arial', sans-serif;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    main()
