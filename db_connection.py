import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor
from sqlalchemy import create_engine

class db_operations():

    def __init__(self):
        self.db_uri = '***' 

    def establish_psycopg_connection(self, cursor_factory = None):
        Psy_conn = psycopg2.connect(self.db_uri)
        Psy_conn.autocommit = True
        cursor = Psy_conn.cursor(cursor_factory=cursor_factory) 
        return cursor, Psy_conn

    def establish_sqlal_connection(self):
        engine = create_engine(self.db_uri)
        conn = engine.connect()
        return conn

    def get_test_question(self, level, questions_to_exclude):
        conn = self.establish_sqlal_connection()

        # Creating a parameterized query string
        parametrized_query = f"SELECT * FROM test_questions WHERE level = '%(level)s'"
        
        # Adding the condition to exclude specific questions if there are any to exclude
        if questions_to_exclude:
            excluded_questions = ", ".join([str(id) for id in questions_to_exclude])
            parametrized_query += f" AND id NOT IN ({excluded_questions})"
        
        # Fetch data using Pandas
        df = pd.read_sql_query(parametrized_query, conn, params={'level': level})

        self.close_sqlal_connection(conn)
        
        if df.empty:
            return None  # Return None if there are no questions left
        
        # Get a random row
        random_row = df.sample(n=1)
        
        # Convert the selected row to a dictionary
        selected_question = random_row.iloc[0].to_dict()
        
        return selected_question

    def get_lesson_question(self, lesson_id, last_question_id):
        conn = self.establish_sqlal_connection()

        # Fetch data using Pandas
        query = f"SELECT * FROM lesson_questions WHERE id = '%(id)s' AND lesson_id = '{lesson_id}'"
        df = pd.read_sql_query(query, conn, params={'id': int(last_question_id)+1})
        print(df)
        self.close_sqlal_connection(conn)

        if df.empty:
            return None  # Return None if there are no questions left
        
        # Convert the selected row to a dictionary
        selected_question = df.iloc[0].to_dict()
        
        return selected_question

    def close_psycopg_connection(self, cursor, Psy_conn):
        cursor.close()
        Psy_conn.close()

    def close_sqlal_connection(self, conn):
        conn.close()