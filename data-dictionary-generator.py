"""
This is the main module of the application. It uses the Streamlit library to create a web-based user interface.

Streamlit is an open-source Python library that makes it easy to create and share beautiful, custom web apps
for machine learning and data science.

The main function of this module is to import the Streamlit library and use its functions to create the application.

Functions:
    main: The main function of the application.
"""

import os
import json
import streamlit as st
import gspread
from google.oauth2 import service_account
import boto3
from snowflake.snowpark import Session

AWS_ACCESS_ID = os.getenv("AWS_ACCESS_ID")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_REGION = os.getenv("SECRETS_AWS_REGION")

SNOWSQL_ACCOUNT = None
SNOWSQL_USER = None
SNOWSQL_PWD = None
SNOWSQL_WAREHOUSE = None
SNOWSQL_DATA_LAKE = None
GC_SERVICE_ACCOUNT_CREDENTIALS = None


def update_secrets(secret_manager) -> None:
    """
    Update necessary credentials from AWS Secrets Manager.

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
    GC_SERVICE_ACCOUNT_CREDENTIALS = secret["GC_SERVICE_ACCOUNT_CREDENTIALS"]


def get_snowflake_session(account, user, pwd):
    connection_parameters = {"account": account, "user": user, "password": pwd}
    return Session.builder.configs(connection_parameters).create()


def get_df_from_sql(session, query):
    return session.sql(query)


def open_google_sheets_client(google_sheets_json_key: str) -> gspread.Client:
    """
    Open a Google Sheet client.

    Documentation on setting up a new project here:
        https://gspread.readthedocs.io/en/latest/oauth2.html#enable-api-access-for-a-project. The project will need
        to have Google Drive API enabled.

    Args:
        google_sheets_json_key(str): Authorization JSON to access the requested spreadsheets.

    Returns: client(gspread.Client): API access to Google Sheets.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = service_account.Credentials.from_service_account_info(
        json.loads(google_sheets_json_key), scopes=scope
    )
    client = gspread.authorize(creds)
    return client


def save_survey_data_to_google_sheets(survey_data, spreadsheet_url):
    """
    Saves the survey data to Google Sheets.

    Args:
        survey_data (pandas.DataFrame): The survey data to be saved.

    Returns:
        None
    """
    client = open_google_sheets_client(GC_SERVICE_ACCOUNT_CREDENTIALS)
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
    snowSession = get_snowflake_session(SNOWSQL_ACCOUNT, SNOWSQL_USER, SNOWSQL_PWD)
    survey_id = st.text_input("Enter the Survey ID")
    spreadsheet_name = st.text_input("Enter the Survey Notebook URL")
    query = f"select * from dw_prod.reporting.data_dictionary where survey_id = '{survey_id}'"
    if len(survey_id) > 0:
        survey_data = get_df_from_sql(snowSession, query).to_pandas()
        st.dataframe(survey_data)
        gsheets = st.button("Save the Data Dictionary into the Survey Notebook")
        if gsheets:
            save_survey_data_to_google_sheets(survey_data, spreadsheet_name)


if __name__ == "__main__":
    main()
