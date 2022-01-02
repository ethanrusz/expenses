import calendar
import datetime

import streamlit as st
import pymongo
import pandas as pd


def get_data(db) -> pd.DataFrame:
    """Fetch the food data from MongoDB.

    :return: Food data as DataFrame.
    """
    df = pd.DataFrame(list(db.food.find({}, {"_id": 0})))  # Fetch data as dataframe
    df['date'] = pd.to_datetime(df['date'])  # Convert to datetime
    return df


def validate_expense(document) -> bool:
    """Check if fields are missing from the form.

    :param document: document to check
    :return: bool, true if valid
    """
    if document['cost'] > 0 and document['location'] != "":
        return True
    else:
        if document['cost'] == 0:
            # No cost was entered
            st.error('Cost cannot be zero!')
        if document['location'] == "":
            # No location was entered
            st.error('You must enter a location!')
        if document['comment'] == "":
            # No comment was entered
            st.warning('A comment is recommended.')
        return False


def insert_expense(db, document) -> None:
    try:
        db.food.insert_one(document)
        st.info('Row inserted successfully!')
    except TypeError:
        st.error('A type error occurred.')


def main():
    st.set_page_config('Grocery Expense Tracker', '🍔')
    client = pymongo.MongoClient(st.secrets['mongo']['uri'])
    db = client.expenses
    df_expenses = get_data(db)  # Get food data to display

    st.markdown('# Grocery Expense Tracker')
    with st.form(key='insert', clear_on_submit=True):  # Create insert form
        st.markdown('## Insert New Expense')
        form_col_1, form_col_2 = st.columns(2)  # Define columns in form
        with form_col_1:
            date = st.date_input('Date', datetime.date.today(), None, datetime.date.today())
            date = datetime.datetime.combine(date, datetime.time())  # Convert from date to datetime
        with form_col_2:
            cost = st.number_input('Cost', 0.00, None, 0.00, 1.00)
            cost = round(cost, 2)  # Round to two decimal places
            gift_card = st.checkbox('Gift Card')
        location = st.text_input('Location').strip()
        comment = st.text_area('Comment').strip()

        insert_button = st.form_submit_button('Insert')

    if insert_button:
        expense = {  # Build the document to insert
            "date": date,
            "cost": cost,
            "location": location,
            "comment": comment,
            "gift": gift_card,
        }

        if validate_expense(expense):
            insert_expense(db, expense)
            df_expenses = get_data(db)  # Refresh overview section

    st.markdown('## Data Overview')
    st.markdown('### Data by Date Range')
    # Select current month by default
    date_range = st.date_input('Query Range', [datetime.date.today().replace(day=1),
                                               datetime.date.today().replace(
                                                   day=calendar.monthrange(date.year, date.month)[1])])
    # Filter dataframe by date selection
    df_range = df_expenses[
        (df_expenses['date'].dt.date >= date_range[0]) & (df_expenses['date'].dt.date <= date_range[1])]

    range_total = df_range['cost'].sum()  # Find total cost in range
    range_gift_total = df_range[(df_range['gift'])]['cost'].sum()  # Find gift card sum in range
    st.markdown(
        "In the selected range you have spent **${total:.2f}**. "
        "Of that total, **${gift:.2f}** was charged to gift cards.".format(
            total=range_total, gift=range_gift_total))

    st.markdown('#### Rows Within Date Range')
    st.dataframe(df_range)

    st.markdown('### All Data')
    total = df_expenses['cost'].sum()  # Find total cost
    gift_total = df_expenses[(df_expenses['gift'])]['cost'].sum()  # Find gift card sum
    st.markdown(
        "Overall you have spent **${total:.2f}**. "
        "Of that total, **${gift:.2f}** was charged to gift cards.".format(
            total=total, gift=gift_total))

    st.markdown('#### All Rows')
    st.dataframe(df_expenses)


if __name__ == '__main__':
    main()
