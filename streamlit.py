import streamlit as st
import sqlite3
import pandas as pd
import os
import base64

def set_background_image_local(image_path):
    with open(image_path, "rb") as file:
        data = file.read()
    base64_image = base64.b64encode(data).decode("utf-8")
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{base64_image}");
            background-size: cover;
            background-position: fit;
            background-repeat: repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background_image_local(r"matrix-style.avif")
# Function to connect to the PostgreSQL database
@st.cache_data
def load_data():
    df1 = pd.read_csv(r"order.csv")  
    df2 = pd.read_csv(r"product.csv")
    return df1, df2

df1, df2 = load_data()

# Function to execute a query and return the result as a pandas DataFrame
def run_query(query):
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    df1.to_sql("order_data", conn, index=False, if_exists="replace")
    df2.to_sql("product_data", conn, index=False, if_exists="replace")
    if conn is None:
        return None  # Return None if connection failed

    try:
        df_result = pd.read_sql_query(query, conn)
        return df_result
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return None
    finally:
        conn.close()

# Home Page
def Retail_order():
    st.title("Retail_order_data Bussiness-In-Site")
    queries = {
        
        "Top-Selling Products":"""
        select p.product_id,p.sub_category,sum(o.sale_price),rank() 
        over(order by sum(o.sale_price) desc) as rank from product_data p 
        join order_data o on
        p.product_id=o.product_id group by p.product_id;
        """,
        "Monthly Sales Analysis":"""
        with y1 as (select order_month,order_year,sum(sale_price) as mom
        from order_data where order_year = 2023 group by order_month,order_year),
        y2 as (select order_month,order_year,sum(sale_price) as mom
        from order_data where order_year = 2022 group by order_month,order_year)
        
        select y1.order_month,(((y1.mom - y2.mom) / y2.mom) * 100) as Monthly_Sales_Analysis,
        rank() over(order by (((y1.mom - y2.mom) / y2.mom) * 100) desc)
        from y1 y1 join y2 y2 on y1.order_month=y2.order_month and 
        y1.order_year=y2.order_year+1;
        """,
        "Product Performance":"""
        select p.product_id,p.category, round(sum(o.sale_price),2)as 
        total_revenue,round(sum(o.profit),2) as total_profit, case 
        when sum(o.sale_price) = 0 then 0 else round((sum(o.profit)/ 
        sum(o.sale_price))*100) end as profit_margin,case when sum(sale_price) 
        > 10000 then 'High perfomer' when sum(sale_price) between 5000 and 10000 then 'Mid Performer' else 'Low Performer'
        end as PerformanceCategory,rank() over(order by sum(o.sale_price) desc)
        from product_data p join order_data o on p.product_id=o.product_id group 
        by p.product_id;
        """,
        "Regional Sales Analysis":"""
        select region, round(sum(order_id), 2) as Total_order, 
        round(sum(sale_price),2) as Total_sale, sum(profit) as 
        Total_profit,round((sum(profit)/ sum(sale_price))*100) as profit_margin,
        rank() over(order by round(sum(sale_price),2) desc) from 
        order_data group by region;
        """,
        "Discount Analysis":"""
        select product_id,sum(quantity) as total_quantity,sum(discount_percent)
        as Total_D_percent, round(sum(discount_price),2) as 
        total_discount,round(sum(sale_price),2) as total_sale,
        round((sum(discount_price)/sum(sale_price))* 100,2)
        as discountimpactpercentage from order_data group by product_id having
        sum(discount_percent)>20 order by discountimpactpercentage desc;
        """

    }

    # Display queries and their results
    for desc, query in queries.items():
        st.subheader(desc)  # Show the query description
        st.code(query, language="sql")  # Show the query
        try:
            result_df = run_query(query)
            if result_df is not None:
                st.dataframe(result_df)  # Show the result as a dataframe
            else:
                st.error(f"Failed to fetch results for '{desc}'.")
        except Exception as e:
            st.error(f"Error running query '{desc}': {e}")

# Query Page
def query_page():
    st.title("Query Page")
    st.write("This page runs SQL queries.")

    # List of queries with descriptions
    queries = {
        "Top 10 Products by Revenue": """
            SELECT p.product_id, p.sub_category, SUM(o.sale_price) AS revenue 
            FROM product_data p 
            JOIN order_data o ON p.product_id = o.product_id 
            GROUP BY p.product_id 
            ORDER BY revenue DESC 
            LIMIT 10;
        """,
        "Top 5 Cities by Profit Margin": """
            SELECT city, AVG(
                CASE WHEN sale_price = 0 THEN 0 ELSE ((profit / sale_price) * 100) END
            ) AS profit_margin 
            FROM order_data 
            GROUP BY city 
            ORDER BY profit_margin DESC 
            LIMIT 5;
        """,
        "Total Discount by Category": """
            SELECT p.category, SUM(o.discount_price * o.quantity) AS total_discount 
            FROM product_data p 
            JOIN order_data o ON p.product_id = o.product_id 
            GROUP BY p.category;
        """,
        "Average Sale Price by Category": """
            SELECT p.category, AVG(o.sale_price) AS Avg_saleprice 
            FROM order_data o 
            JOIN product_data p ON p.product_id = o.product_id 
            GROUP BY category;
        """,
        "Region with Highest Average Sales": """
            SELECT region, AVG(sale_price) AS avg_sales 
            FROM order_data 
            GROUP BY region 
            ORDER BY avg_sales DESC 
            LIMIT 1;
        """,
        "Total Profit by Category": """
            SELECT p.category, SUM(o.profit) AS total_profit 
            FROM product_data p 
            JOIN order_data o ON p.product_id = o.product_id 
            GROUP BY p.category;
        """,
        "Highest Quantity Sold by Segment": """
            SELECT segment, SUM(quantity) AS highest_quantity  
            FROM order_data 
            GROUP BY segment 
            ORDER BY highest_quantity DESC;
        """,
        "Average Discount by Region": """
            SELECT region, ROUND(AVG(discount_percent), 2) AS avg_discount 
            FROM order_data 
            GROUP BY region;
        """,
        "Most Profitable Category": """
            SELECT p.category, ROUND(SUM(o.profit), 2) AS total_profit 
            FROM product_data p 
            JOIN order_data o ON p.product_id = o.product_id 
            GROUP BY p.category 
            ORDER BY total_profit DESC 
            LIMIT 1;
        """,
        "Annual Revenue": """
            SELECT order_year, ROUND(SUM(sale_price), 2) AS Revenue_per_year 
            FROM order_data 
            GROUP BY order_year;
        """
    }

    # Display queries and their results
    for desc, query in queries.items():
        st.subheader(desc)  # Show the query description
        st.code(query, language="sql")  # Show the query
        try:
            result_df = run_query(query)
            if result_df is not None:
                st.dataframe(result_df)  # Show the result as a dataframe
            else:
                st.error(f"Failed to fetch results for '{desc}'.")
        except Exception as e:
            st.error(f"Error running query '{desc}': {e}")

# About Page
def My_Query():
    st.title("Custom Queries for the Dataset")
    st.write("Learn more about this Dataset.")

    queries = {
        "Identify the top 5 states with the highest total sales revenue, grouped by category":"""
        select o.state, p.product_id,p.category,round(sum(o.sale_price),2) as sale_price
        from order_data o join product_data p on o.product_id=p.product_id group by state,p.product_id
        order by sum(sale_price) desc limit 5;
        """,
        "Calculate the Total Number of Orders, Quantity, and Revenue for Each Product Category":"""
        select p.category,sum(o.order_id) as order_count,o.quantity,round(sum(o.sale_price),2)
        as revenue from product_data p join order_data o on p.product_id=o.product_id group by p.category,o.quantity;
        """,
        "Identify the top 10 products with the highest quantities sold, along with their total revenue and profit":"""
        select p.product_id, p.category, sum(o.quantity) as Total_quantity,
        round(sum(o.sale_price),2) as Revenue, round(sum(o.profit),2) as profit from 
        product_data p join order_data o on p.product_id=o.product_id group by 
        p.product_id order by sum(o.quantity) desc limit 10;
        """,
        "Rank all regions by the total quantity of products sold, including the total number of orders":"""
        select o.region, sum(o.quantity) as total_quantity, count(o.order_id) as order_count,
        rank() over(order by sum(quantity) desc) from order_data o join 
        product_data p on p.product_id=o.product_id group by o.region;
        """,
        "Determine the Top 3 Customers Based on Their Total Profit Contribution":"""
        select segment, round(sum(profit),2) as profit, rank() 
        over(order by sum(profit) desc) from order_data group by segment;
        """,
        "Determine the Average Quantity Ordered Per Product":"""
        select p.sub_category, round(avg(o.quantity),2) as Avg_quantity,
        count(o.order_id) as total_order from product_data p join order_data o on 
        o.product_id=p.product_id group by p.sub_category;
        """,
        "Analysis of Total Revenue Generated by Each Segment":"""
        select segment, round(sum(sale_price),2) as total_revenue 
        from order_Data group by segment;
        """,
        "Calculate the total profit for all regions":"""
        select region, round(sum(profit),2) as Total_profit from order_Data 
        group by region order by sum(profit) desc;
        """,
        "Which state placed the highest quantity of orders, and what was the corresponding shipping mode?":"""
        select state, sum(quantity) as Total_quanity, ship_mode from order_data 
        group by state,ship_mode order by sum(quantity) desc;
        """,
        "Identify the Month with the Highest Revenue":"""
        select order_month, round(sum(sale_price),2) as profit,
        rank() over(order by sum(sale_price) desc) from order_data group 
        by order_month;"""
    }

    # Display queries and their results
    for desc, query in queries.items():
        st.subheader(desc)  # Show the query description
        st.code(query, language="sql")  # Show the query
        try:
            result_df = run_query(query)
            if result_df is not None:
                st.dataframe(result_df)  # Show the result as a dataframe
            else:
                st.error(f"Failed to fetch results for '{desc}'.")
        except Exception as e:
            st.error(f"Error running query '{desc}': {e}")


# Dropdown for navigation
page = st.sidebar.selectbox("Select a page", ["Retail_order", "Query", "My_Query"])

# Render the selected page
if page == "Retail_order":
    Retail_order()
elif page == "Query":
    query_page()
elif page == "My_Query":
    My_Query()
elif page=="write_query":
    write_query()
