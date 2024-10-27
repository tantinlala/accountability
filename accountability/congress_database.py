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
        create_recent_roll_call_sql = """ 
            CREATE TABLE IF NOT EXISTS RecentRollCall (
                Year INTEGER PRIMARY KEY,
                RollCallID INTEGER NOT NULL
            ); 
        """
        create_rollcalls_sql = """ 
            CREATE TABLE IF NOT EXISTS RollCalls (
                RollCallID TEXT PRIMARY KEY,
                DateTime DATETIME,
                Question TEXT,
                BillName TEXT,
                AmendmentName TEXT
            ); 
        """
        create_congressmen_sql = """ 
            CREATE TABLE IF NOT EXISTS Congressmen (
                CongressmanID TEXT PRIMARY KEY,
                Name TEXT NOT NULL,
                State TEXT NOT NULL
            ); 
        """
        create_votes_sql = """ 
            CREATE TABLE IF NOT EXISTS Votes (
                VoteID INTEGER PRIMARY KEY AUTOINCREMENT,
                RollCallID TEXT NOT NULL,
                CongressmanID TEXT NOT NULL,
                Vote TEXT NOT NULL,
                FOREIGN KEY (RollCallID) REFERENCES RollCalls (RollCallID),
                FOREIGN KEY (CongressmanID) REFERENCES Congressmen (CongressmanID)
            ); 
        """

        try:
            c = self.conn.cursor()
            c.execute(create_recent_roll_call_sql)
            c.execute(create_rollcalls_sql)
            c.execute(create_congressmen_sql)
            c.execute(create_votes_sql)
        except sqlite3.Error as e:
            print(e)

    def update_hr_roll_call_id(self, year, roll_call_id):
        """Update the roll call ID for a given year."""
        sql = """ 
            INSERT INTO RecentRollCall(Year, RollCallID)
            VALUES(?, ?)
            ON CONFLICT(Year) DO UPDATE SET RollCallID = excluded.RollCallID; 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (year, roll_call_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def get_most_recent_hr_roll_call_id(self, year):
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

    def insert_roll_call(self, roll_call_id, datetime, question, bill_name, amendment_name):
        """Insert a roll call into the database."""
        sql = """ 
            INSERT INTO RollCalls(RollCallID, DateTime, Question, BillName, AmendmentName)
            VALUES(?, ?, ?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (roll_call_id, datetime, question, bill_name, amendment_name))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def insert_congressman(self, congressman_id, name, state):
        """Insert a congressman into the database."""
        sql = """ 
            INSERT INTO Congressmen(CongressmanID, Name, State)
            VALUES(?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (congressman_id, name, state))
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

    def insert_vote(self, roll_call_id, congressman_id, vote):
        """Insert a vote into the database."""
        sql = """ 
            INSERT INTO Votes(RollCallID, CongressmanID, Vote)
            VALUES(?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (roll_call_id, congressman_id, vote))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def find_all_votes_from_previous_roll_call(self, roll_call_id):
        """Find all votes from a previous roll call."""
        # First, get the roll call ID that precedes the provided roll call ID that
        # has the same bill name and question.

        # TODO

        sql = "SELECT * FROM Votes WHERE RollCallID = ?"
        try:
            c = self.conn.cursor()
            c.execute(sql, (roll_call_id,))
            return c.fetchall()
        except sqlite3.Error as e:
            print(e)
        return None