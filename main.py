"""
This is the main module of the application. It uses the Streamlit library to create a web-based user interface.

Streamlit is an open-source Python library that makes it easy to create and share beautiful, custom web apps
for machine learning and data science.

The main function of this module is to import the Streamlit library and use its functions to create the application.

Functions:
    main: The main function of the application.
"""

import streamlit as st
from toolkit.env import EnvironmentVariableManager
from toolkit.googlesheets import open_google_sheets_client
from toolkit.snowflakedb import SnowflakeDB


def save_survey_data_to_google_sheets(survey_data, spreadsheet_url):
    """
    Saves the survey data to Google Sheets.

    Args:
        survey_data (pandas.DataFrame): The survey data to be saved.

    Returns:
        None
    """
    gsheets_service_account = EnvironmentVariableManager().getenv(
        "GSHEETS_SERVICE_ACCOUNT"
    )
    # Get the GSheets client using the toolkit
    client = open_google_sheets_client(gsheets_service_account)
    # Recycle the Service Account credentials object
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
