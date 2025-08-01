import streamlit as st

from aws.dynamodb_connector import DynamoDBConnector

DynamoDBConnector().initiate_connection()

pg = st.navigation(pages=[
    st.Page("views/dashboard.py", title="Главная"),
    st.Page("views/status_control.py", title="Управление состоянием"),
    ], position="top")

pg.run()
