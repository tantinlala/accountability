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
            Question TEXT NOT NULL,
            BillName TEXT NOT NULL,
            AmendmentName TEXT,
            CONSTRAINT RollCallYearID PRIMARY KEY (RollCallID, Year)
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

    def add_rollcall_data(self, rollcall_id, year, question, bill_name, amendment_name):
        """Insert a roll call into the database."""
        sql = """ 
            INSERT INTO RollCalls(RollCallID, Year, Question, BillName, AmendmentName)
            VALUES(?, ?, ?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (rollcall_id, year, question, bill_name, amendment_name))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def add_congressman(self, congressman_id, name, state, party):
        """Insert a congressman into the database."""
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

    def add_vote(self, rollcall_id, congressman_id, vote):
        """Insert a vote into the database."""
        sql = """ 
            INSERT INTO Votes(RollCallID, CongressmanID, Vote)
            VALUES(?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (rollcall_id, congressman_id, vote))
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