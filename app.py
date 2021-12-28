import datetime

import streamlit as st
import pymongo
import pandas as pd
import altair as alt


def get_data(client) -> pd.DataFrame:
    """Fetch the food data from MongoDB.

    :return: Food data as DataFrame.
    """
    db = client.expenses
    df = pd.DataFrame(list(db.food.find({}, {"_id": 0})))  # Fetch data as dataframe
    df['date'] = pd.to_datetime(df['date'])  # Convert from string to datetime
    return df


def main():
    st.set_page_config('Food Cost Tracker', '🍔')
    client = pymongo.MongoClient(st.secrets['mongo']['uri'])
    df_food = get_data(client)  # Get food data to display

    st.markdown('# Food Cost Tracker')
    with st.form(key='insert', clear_on_submit=True):  # Create insert form
        st.markdown('## Insert New Expense')
        col1, col2 = st.columns(2)  # Define columns in form
        with col1:
            date = st.date_input('Date', datetime.date.today(), None, datetime.date.today())
            date = datetime.datetime.combine(date, datetime.time())  # Convert from date to datetime
        with col2:
            cost = st.number_input('Cost', 0.00, None, 0.00, 1.00)
            cost = round(cost, 2)  # Round to two decimal places
            gift_card = st.checkbox('Gift Card')
        location = st.text_input('Location').strip()
        comment = st.text_area('Comment')

        insert_button = st.form_submit_button('Insert')

    document = {  # Build the document to insert
        "date": date,
        "cost": cost,
        "location": location,
        "comment": comment,
        "gift": gift_card,
    }

    if insert_button:
        # When button is pressed validate
        if document['cost'] == 0:
            # No cost was entered
            st.error('Cost cannot be zero!')
        if document['location'] == "":
            # No location was entered
            st.error('You must enter a location!')
        if document['cost'] > 0 and document['cost'] != "":
            # User input is valid insert
            db = client.expenses
            try:
                db.food.insert_one(document)
                st.info('Row inserted successfully!')
            except TypeError:
                st.error('A type error occurred.')

    st.markdown('## Data Overview')
    refresh_button = st.button('Refresh Data')
    if refresh_button:
        df_food = get_data(client)

    st.dataframe(df_food)

    chart = alt.Chart(df_food).mark_line().encode(
        x='date:T',
        y='cost'
    )
    # Chart is hidden for now
    # st.altair_chart(chart, use_container_width=True)


if __name__ == '__main__':
    main()
