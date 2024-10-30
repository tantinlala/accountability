import sqlite3

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
            AmendmentName TEXT
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

        try:
            c = self.conn.cursor()
            c.execute(create_last_hr_rollcall_for_year_sql)
            c.execute(create_hr_rollcalls_sql)
            c.execute(create_congressmen_sql)
            c.execute(create_hr_votes_sql)
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

    def add_rollcall_data(self, rollcall_id, year, action_datetime, question, bill_name, amendment_name):
        """Insert a roll call into the database."""
        # Return if the roll call already exists
        if self.rollcall_exists(action_datetime):
            return

        sql = """ 
            INSERT INTO RollCalls(RollCallID, Year, ActionDateTime, Question, BillName, AmendmentName)
            VALUES(?, ?, ?, ?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (rollcall_id, year, action_datetime, question, bill_name, amendment_name))
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
                rollcall_data['AmendmentName'] = rollcall_meta[5]
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

    def find_all_votes_from_previous_rollcall(self, rollcall_id):
        """Find all votes from a previous roll call."""
        # First, get the roll call ID that precedes the provided roll call ID that
        # has the same bill name and question.

        # TODO

        sql = "SELECT * FROM Votes WHERE RollCallID = ?"
        try:
            c = self.conn.cursor()
            c.execute(sql, (rollcall_id,))
            return c.fetchall()
        except sqlite3.Error as e:
            print(e)
        return None