import sqlite3
from .file_utils import get_datetime_and_name_in_filename
from datetime import datetime

class CongressDatabase:
    def __init__(self, db_name="congress.db"):
        self.db_name = db_name
        self.conn = self.create_connection()
        self.initialize_database()

    def create_connection(self):
        """Create a database connection to the SQLite database."""
        try:
            conn = sqlite3.connect(self.db_name)
            return conn
        except sqlite3.Error as e:
            print(e)
        return None

    def initialize_database(self):
        """Create the tables if they do not exist."""
        create_last_hr_rollcall_for_year_sql = """ 
            CREATE TABLE IF NOT EXISTS RecentRollCall (
                Year INTEGER PRIMARY KEY,
                RollCallID INTEGER NOT NULL
            ); 
        """
        create_hr_rollcalls_sql = """ 
            CREATE TABLE IF NOT EXISTS RollCalls (
            RollCallID INTEGER NOT NULL,
            Year INTEGER NOT NULL,
            ActionDateTime TIMESTAMP PRIMARY KEY,
            Question TEXT NOT NULL,
            BillName TEXT NOT NULL,
            BillDateTime TIMESTAMP NOT NULL,
            AmendmentName TEXT,
            FOREIGN KEY (BillName, BillDateTime) REFERENCES Bills (BillName, BillDateTime)
            ); 
        """
        create_congressmen_sql = """ 
            CREATE TABLE IF NOT EXISTS Congressmen (
                CongressmanID TEXT PRIMARY KEY,
                Name TEXT,
                State TEXT,
                Party TEXT
            ); 
        """
        create_hr_votes_sql = """ 
            CREATE TABLE IF NOT EXISTS Votes (
                CongressmanID TEXT NOT NULL,
                Vote TEXT NOT NULL,
                ActionDateTime TIMESTAMP NOT NULL,
                FOREIGN KEY (ActionDateTime) REFERENCES RollCalls (ActionDateTime),
                FOREIGN KEY (CongressmanID) REFERENCES Congressmen (CongressmanID),
                CONSTRAINT VoteID PRIMARY KEY (ActionDateTime, CongressmanID)
            ); 
        """
        create_crp_categories_sql = """ 
            CREATE TABLE IF NOT EXISTS CRPCategories (
                CatOrder TEXT PRIMARY KEY,
                Industry TEXT NOT NULL
            ); 
        """
        create_bills_sql = """ 
            CREATE TABLE IF NOT EXISTS Bills (
                BillName TEXT NOT NULL,
                BillDateTime TIMESTAMP NOT NULL,
                PRIMARY KEY (BillName, BillDateTime)
            ); 
        """
        try:
            c = self.conn.cursor()
            c.execute(create_last_hr_rollcall_for_year_sql)
            c.execute(create_hr_rollcalls_sql)
            c.execute(create_congressmen_sql)
            c.execute(create_hr_votes_sql)
            c.execute(create_crp_categories_sql)
            c.execute(create_bills_sql)
        except sqlite3.Error as e:
            print(e)

    def update_last_hr_rollcall_for_year(self, year, rollcall_id):
        """Update the roll call ID for a given year."""
        sql = """ 
            INSERT INTO RecentRollCall(Year, RollCallID)
            VALUES(?, ?)
            ON CONFLICT(Year) DO UPDATE SET RollCallID = excluded.RollCallID; 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (year, rollcall_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def year_exists(self, year):
        """Check if a year exists in the database."""
        sql = "SELECT * FROM RecentRollCall WHERE Year = ?"
        try:
            c = self.conn.cursor()
            c.execute(sql, (year,))
            return c.fetchone() is not None
        except sqlite3.Error as e:
            print(e)
        return False

    def add_year(self, year):
        """Initialize the roll call ID for a given year."""
        sql = """ 
            INSERT INTO RecentRollCall(Year, RollCallID)
            VALUES(?, 0); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (year,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def get_last_hr_rollcall_for_year(self, year):
        """Retrieve the most recent roll call ID for a given year."""
        sql = "SELECT RollCallID FROM RecentRollCall WHERE Year = ?"
        try:
            c = self.conn.cursor()
            c.execute(sql, (year,))
            result = c.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(e)
        return None

    def rollcall_exists(self, action_datetime):
        """Check if a roll call exists in the database."""
        sql = "SELECT * FROM RollCalls WHERE ActionDateTime = ?"
        try:
            c = self.conn.cursor()
            c.execute(sql, (action_datetime,))
            return c.fetchone() is not None
        except sqlite3.Error as e:
            print(e)
        return False

    def add_rollcall_data(self, rollcall_id, year, action_datetime, question, bill_name, bill_datetime, amendment_name):
        """Insert a roll call into the database."""

        self.add_bill(bill_name, bill_datetime)

        # Return if the roll call already exists
        if self.rollcall_exists(action_datetime):
            return

        sql = """ 
            INSERT INTO RollCalls(RollCallID, Year, ActionDateTime, Question, BillName, BillDateTime, AmendmentName)
            VALUES(?, ?, ?, ?, ?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (rollcall_id, year, action_datetime, question, bill_name, bill_datetime, amendment_name))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def add_bill(self, bill_name, bill_datetime):
        """Insert a bill into the database."""
        sql = """ 
            INSERT INTO Bills(BillName, BillDateTime)
            VALUES(?, ?)
            ON CONFLICT(BillName, BillDateTime) DO NOTHING; 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (bill_name, bill_datetime))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def get_rollcall_data(self, rollcall_id, year):
        """Retrieve all meta data for roll call as well as each vote and pack it up into a dictionary"""
        rollcall_data = {}
        
        # Get roll call meta data
        rollcall_sql = "SELECT * FROM RollCalls WHERE RollCallID = ? AND Year = ?"
        try:
            c = self.conn.cursor()
            c.execute(rollcall_sql, (rollcall_id, year))
            rollcall_meta = c.fetchone()
            if rollcall_meta:
                rollcall_data['RollCallID'] = rollcall_meta[0]
                rollcall_data['Year'] = rollcall_meta[1]
                rollcall_data['ActionDateTime'] = rollcall_meta[2]
                rollcall_data['Question'] = rollcall_meta[3]
                rollcall_data['BillName'] = rollcall_meta[4]
                rollcall_data['BillDateTime'] = datetime.strptime(rollcall_meta[5], '%Y-%m-%d %H:%M:%S')
                rollcall_data['AmendmentName'] = rollcall_meta[6]
            else:
                return None
        except sqlite3.Error as e:
            print(e)
            return None

        # Get votes for the roll call
        votes_sql = "SELECT * FROM Votes WHERE ActionDateTime = ?"
        try:
            c.execute(votes_sql, (rollcall_data['ActionDateTime'],))
            votes = c.fetchall()
            rollcall_data['Votes'] = [{'CongressmanID': vote[0], 'Vote': vote[1]} for vote in votes]
        except sqlite3.Error as e:
            print(e)
            return None

        # Add congressman's name, state, and party to each vote
        for vote in rollcall_data['Votes']:
            congressman_sql = "SELECT * FROM Congressmen WHERE CongressmanID = ?"
            try:
                c.execute(congressman_sql, (vote['CongressmanID'],))
                congressman = c.fetchone()
                vote['Name'] = congressman[1]
                vote['State'] = congressman[2]
                vote['Party'] = congressman[3]
            except sqlite3.Error as e:
                print(e)
                return None

        # Format ActionDateTime in the following format: YYYY-MM-DDTHH:MM:SSZ
        rollcall_data['ActionDateTime'] = rollcall_data['ActionDateTime'].replace(" ", "T") + "Z"

        # Sort votes by state in alphabetical order
        rollcall_data['Votes'] = sorted(rollcall_data['Votes'], key=lambda x: x['State'])

        return rollcall_data


    def add_congressman(self, congressman_id, name, state, party):
        """Insert a congressman into the database."""
        # Return if the congressman already exists
        if self.congressman_exists(congressman_id):
            return

        sql = """ 
            INSERT INTO Congressmen(CongressmanID, Name, State, Party)
            VALUES(?, ?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (congressman_id, name, state, party))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def congressman_exists(self, congressman_id):
        """Check if a congressman exists in the database."""
        sql = "SELECT * FROM Congressmen WHERE CongressmanID = ?"
        try:
            c = self.conn.cursor()
            c.execute(sql, (congressman_id,))
            return c.fetchone() is not None
        except sqlite3.Error as e:
            print(e)
        return False

    def vote_exists(self, action_datetime, congressman_id):
        """Check if a vote exists in the database."""
        sql = "SELECT * FROM Votes WHERE ActionDateTime = ? AND CongressmanID = ?"
        try:
            c = self.conn.cursor()
            c.execute(sql, (action_datetime, congressman_id))
            return c.fetchone() is not None
        except sqlite3.Error as e:
            print(e)
        return False

    def add_vote(self, action_datetime, congressman_id, vote):
        if self.vote_exists(action_datetime, congressman_id):
            return

        """Insert a vote into the database."""
        sql = """ 
            INSERT INTO Votes(ActionDateTime, CongressmanID, Vote)
            VALUES(?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (action_datetime, congressman_id, vote))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def get_previous_rollcall_data(self, rollcall_id, year):
        """Retrieve the previous roll call data with the same question but a different version of the bill."""
        try:
            # Get the current roll call's bill name
            current_bill_sql = "SELECT BillName, AmendmentName, Question FROM RollCalls WHERE RollCallID = ? AND Year = ?"
            c = self.conn.cursor()
            c.execute(current_bill_sql, (rollcall_id, year))
            present_rollcall_data = c.fetchone()
            if not present_rollcall_data:
                return None

            bill_name = present_rollcall_data[0]
            amendment_name = present_rollcall_data[1]
            question = present_rollcall_data[2]

            # Query for the previous roll call data
            sql = """
                SELECT * FROM RollCalls
                WHERE Question = ? 
                AND ((RollCallID < ? AND Year = ?) OR Year < ?)
                AND BillName = ?
                AND (AmendmentName = ? OR (AmendmentName IS NULL AND ? IS NULL))
                ORDER BY Year DESC, RollCallID DESC
                LIMIT 1
            """
            c.execute(sql, (question, rollcall_id, year, year, bill_name, amendment_name, amendment_name))
            previous_rollcall_meta = c.fetchone()
            if not previous_rollcall_meta:
                return None

            previous_rollcall_data = {
                'RollCallID': previous_rollcall_meta[0],
                'Year': previous_rollcall_meta[1],
                'ActionDateTime': datetime.strptime(previous_rollcall_meta[2], '%Y-%m-%d %H:%M:%S'),
                'Question': previous_rollcall_meta[3],
                'BillName': previous_rollcall_meta[4],
                'BillDateTime': datetime.strptime(previous_rollcall_meta[5], '%Y-%m-%d %H:%M:%S'),
                'AmendmentName': previous_rollcall_meta[6],
                'Votes': []
            }

            votes_sql = "SELECT * FROM Votes WHERE ActionDateTime = ?"
            c.execute(votes_sql, (previous_rollcall_data['ActionDateTime'],))
            votes = c.fetchall()
            previous_rollcall_data['Votes'] = [{'CongressmanID': vote[0], 'Vote': vote[1]} for vote in votes]

            for vote in previous_rollcall_data['Votes']:
                congressman_sql = "SELECT * FROM Congressmen WHERE CongressmanID = ?"
                c.execute(congressman_sql, (vote['CongressmanID'],))
                congressman = c.fetchone()
                vote['Name'] = congressman[1]
                vote['State'] = congressman[2]
                vote['Party'] = congressman[3]

            previous_rollcall_data['ActionDateTime'] = previous_rollcall_data['ActionDateTime'].replace(" ", "T") + "Z"
            previous_rollcall_data['Votes'] = sorted(previous_rollcall_data['Votes'], key=lambda x: x['State'])

            return previous_rollcall_data
        except sqlite3.Error as e:
            print(e)
            return None

    def add_crp_category(self, catorder, industry):
        """Insert a CRP category into the database."""
        sql = """ 
            INSERT INTO CRPCategories(CatOrder, Industry)
            VALUES(?, ?)
            ON CONFLICT(CatOrder) DO UPDATE SET Industry = excluded.Industry; 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (catorder, industry))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def get_all_industries(self):
        """Retrieve all industries from the CRPCategories table."""
        sql = "SELECT Industry FROM CRPCategories"
        try:
            c = self.conn.cursor()
            c.execute(sql)
            industries = [row[0] for row in c.fetchall()]
            return industries
        except sqlite3.Error as e:
            print(e)
            return []