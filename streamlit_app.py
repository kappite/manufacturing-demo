import streamlit as st
import pandas as pd
import snowflake.connector
import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Use environment variables
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE')
SNOWFLAKE_SCHEMA = os.getenv('SNOWFLAKE_SCHEMA')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')

# Azure OpenAI API configurations
AZURE_OPENAI_ENDPOINT = "https://aoa-ai-demo2.openai.azure.com/"
AZURE_OPENAI_API_VERSION = "2023-12-01-preview"
AZURE_OPENAI_DEPLOYMENT_NAME = "manufacturing-demo"

# Set up OpenAI library to use Azure OpenAI service
openai.api_type = "azure"
openai.api_key = AZURE_OPENAI_API_KEY
openai.api_base = AZURE_OPENAI_ENDPOINT
openai.api_version = AZURE_OPENAI_API_VERSION

# Function to call GPT model on Azure OpenAI
def query_chatgpt(system_prompt, data_prompt):
    response = openai.ChatCompletion.create(
        engine=AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": data_prompt}
        ],
        max_tokens=1000
    )
    return response['choices'][0]['message']['content']

# Function to connect to Snowflake
def connect_to_snowflake():
    return snowflake.connector.connect(
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        account=SNOWFLAKE_ACCOUNT,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA
    )

# Function to run a query using Snowflake connector
def run_query(query):
    conn = connect_to_snowflake()
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    df = pd.DataFrame(result, columns=columns)
    cur.close()
    conn.close()
    return df

# Streamlit app title and description
st.title("Manufacturing Data Dashboard with GPT")
st.write("This app interacts with the manufacturing data stored in the Snowflake database and generates insights using GPT.")

# Option to select which data to view
option = st.selectbox(
    "Choose the data you want to explore",
    ("Production Lines", "Machine Logs", "Failure Incidents", "Product Dimension")
)

# Default system prompt for GPT
default_system_prompt = "Analyze the following manufacturing data and provide insights or suggestions for improvement."

# Allow the user to adjust the system prompt
with st.expander("Adjust system prompt"):
    system_prompt = st.text_area("System instructions", value=default_system_prompt)

# Display Production Lines data
if option == "Production Lines":
    st.header("Production Lines")
    query = "SELECT * FROM MANUFACTURING_DATA.DEMO.Production_Lines"
    data = run_query(query)
    st.dataframe(data, use_container_width=True)

    # Ask GPT for suggestions
    if st.button("Generate GPT Suggestions"):
        data_prompt = data.to_string(index=False)
        gpt_response = query_chatgpt(system_prompt, data_prompt)
        st.subheader("GPT Suggestions")
        st.write(gpt_response)

# Display Machine Logs data with filtering options
elif option == "Machine Logs":
    st.header("Machine Logs")

    # Option to filter by LineID
    line_id = st.selectbox("Select LineID to filter", options=[None] + list(range(1, 11)))

    query = """
    SELECT ml.*, dp.ProductName, dp.Category
    FROM MANUFACTURING_DATA.DEMO.Machine_Logs ml
    JOIN MANUFACTURING_DATA.DEMO.d_product dp ON ml.ProductID = dp.ProductID
    """
    if line_id:
        query += f" WHERE ml.LineID = {line_id}"

    data = run_query(query)
    st.dataframe(data, use_container_width=True)

    # Ask GPT for analysis
    if st.button("Analyze with GPT"):
        data_prompt = data.to_string(index=False)
        gpt_response = query_chatgpt(system_prompt, data_prompt)
        st.subheader("GPT Analysis")
        st.write(gpt_response)

# Display Failure Incidents data with filtering and search options
elif option == "Failure Incidents":
    st.header("Failure Incidents")

    # Option to filter by resolved status
    resolved = st.selectbox("Filter by Resolved Status", options=["All", "True", "False"])

    # Option to search by description
    description_search = st.text_input("Search in Descriptions")

    query = """
    SELECT fi.*, dp.ProductName, dp.Category
    FROM MANUFACTURING_DATA.DEMO.Failure_Incidents fi
    JOIN MANUFACTURING_DATA.DEMO.d_product dp ON fi.ProductID = dp.ProductID
    """
    conditions = []
    if resolved != "All":
        conditions.append(f"fi.Resolved = {resolved}")
    if description_search:
        conditions.append(f"fi.Description ILIKE '%{description_search}%'")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    data = run_query(query)
    st.dataframe(data, use_container_width=True)

    # Ask GPT for failure incident analysis
    if st.button("Get GPT Insights"):
        data_prompt = data.to_string(index=False)
        gpt_response = query_chatgpt(system_prompt, data_prompt)
        st.subheader("GPT Insights")
        st.write(gpt_response)

# Display Product Dimension data
elif option == "Product Dimension":
    st.header("Product Dimension")
    query = "SELECT * FROM MANUFACTURING_DATA.DEMO.d_product"
    data = run_query(query)
    st.dataframe(data, use_container_width=True)

    # Ask GPT for product analysis
    if st.button("Analyze Products with GPT"):
        data_prompt = data.to_string(index=False)
        gpt_response = query_chatgpt(system_prompt, data_prompt)
        st.subheader("GPT Product Insights")
        st.write(gpt_response)
        
