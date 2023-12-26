"""
This is the main module of the application. It uses the Streamlit library to create a web-based user interface.

Streamlit is an open-source Python library that makes it easy to create and share beautiful, custom web apps
for machine learning and data science.

The main function of this module is to import the Streamlit library and use its functions to create the application.

Functions:
    main: The main function of the application.
"""

import json
import streamlit as st
import boto3
from toolkit.env import EnvironmentVariableManager
from toolkit.googlesheets import open_google_sheets_client
from toolkit.snowflakedb import SnowflakeDB

AWS_ACCESS_ID = EnvironmentVariableManager().getenv("AWS_ACCESS_ID")
AWS_ACCESS_KEY = EnvironmentVariableManager().getenv("AWS_ACCESS_KEY")
AWS_REGION = EnvironmentVariableManager().getenv("SECRETS_AWS_REGION")

SNOWSQL_ACCOUNT = None
SNOWSQL_USER = None
SNOWSQL_PWD = None
SNOWSQL_WAREHOUSE = None
SNOWSQL_DATA_LAKE = None
GC_SERVICE_ACCOUNT_CREDENTIALS = None


def update_secrets(secret_manager) -> None:
    """update necessary credentials from AWS Secrets Manager.

    Parameters:
        secret_manager: AWS Secrets Manager object
    """
    secret_value = secret_manager.get_secret_value(
        SecretId="/polco_ardem_ingestion/env"
    )
    secret_string = secret_value["SecretString"]
    secret = json.loads(secret_string)

    global SNOWSQL_ACCOUNT
    SNOWSQL_ACCOUNT = secret["SNOWSQL_ACCOUNT"]
    global SNOWSQL_USER
    SNOWSQL_USER = secret["SNOWSQL_USER"]
    global SNOWSQL_PWD
    SNOWSQL_PWD = secret["SNOWSQL_PWD"]
    global SNOWSQL_WAREHOUSE
    SNOWSQL_WAREHOUSE = secret["SNOWSQL_WAREHOUSE"]
    global GC_SERVICE_ACCOUNT_CREDENTIALS
    GC_SERVICE_ACCOUNT_CREDENTIALS = json.loads(
        secret["GC_SERVICE_ACCOUNT_CREDENTIALS"]
    )


def save_survey_data_to_google_sheets(survey_data, spreadsheet_url):
    """
    Saves the survey data to Google Sheets.

    Args:
        survey_data (pandas.DataFrame): The survey data to be saved.

    Returns:
        None
    """
    gsheets_service_account = EnvironmentVariableManager().getenv(
        "GC_SERVICE_ACCOUNT_CREDENTIALS"
    )
    client = open_google_sheets_client(gsheets_service_account)
    sh = client.open_by_url(spreadsheet_url)
    worksheet = sh.worksheet("Data Dictionary")
    survey_data.fillna(0, inplace=True)
    worksheet.update(
        [survey_data.columns.values.tolist()] + survey_data.values.tolist()
    )
    st.success("Saved to Google Sheets")


def main():
    """
    Main function to run the Streamlit application.
    """
    awsSession = boto3.Session(
        aws_access_key_id=AWS_ACCESS_ID, aws_secret_access_key=AWS_ACCESS_KEY
    )
    secret = awsSession.client("secretsmanager", region_name=AWS_REGION)
    update_secrets(secret)
    st.title("Data Dictionary Generator")
    conn = SnowflakeDB()
    survey_id = st.text_input("Enter the Survey ID")
    spreadsheet_name = st.text_input("Enter the Survey Notebook URL")
    query = f"select * from dw_prod.reporting.data_dictionary where survey_id = '{survey_id}'"
    if len(survey_id) > 0:
        conn.connect()
        survey_data = conn.get_pandas_dataframe(query)
        st.dataframe(survey_data)
        gsheets = st.button("Save the Data Dictionary into the Survey Notebook")
        if gsheets:
            save_survey_data_to_google_sheets(survey_data, spreadsheet_name)


if __name__ == "__main__":
    main()
