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
        create_legislators_sql = """ 
            CREATE TABLE IF NOT EXISTS Legislators (
                LegislatorID TEXT PRIMARY KEY,
                Name TEXT,
                State TEXT,
                Party TEXT
            ); 
        """
        create_hr_votes_sql = """ 
            CREATE TABLE IF NOT EXISTS Votes (
                LegislatorID TEXT NOT NULL,
                Vote TEXT NOT NULL,
                ActionDateTime TIMESTAMP NOT NULL,
                FOREIGN KEY (ActionDateTime) REFERENCES RollCalls (ActionDateTime),
                FOREIGN KEY (LegislatorID) REFERENCES Legislators (LegislatorID),
                CONSTRAINT VoteID PRIMARY KEY (ActionDateTime, LegislatorID)
            ); 
        """
        create_industries_sql = """ 
            CREATE TABLE IF NOT EXISTS Industries (
                ID TEXT PRIMARY KEY,
                Description TEXT NOT NULL
            ); 
        """
        create_bills_sql = """ 
            CREATE TABLE IF NOT EXISTS Bills (
                BillName TEXT NOT NULL,
                BillDateTime TIMESTAMP NOT NULL,
                BillTitle TEXT,
                PRIMARY KEY (BillName, BillDateTime)
            ); 
        """
        create_bill_industries_sql = """ 
            CREATE TABLE IF NOT EXISTS BillIndustries (
                BillName TEXT NOT NULL,
                IndustryID TEXT NOT NULL,
                FOREIGN KEY (BillName) REFERENCES Bills (BillName),
                FOREIGN KEY (IndustryID) REFERENCES Industries (ID),
                PRIMARY KEY (BillName, IndustryID)
            ); 
        """
        create_legislator_donors_sql = """ 
            CREATE TABLE IF NOT EXISTS LegislatorIndustries (
                LegislatorID TEXT NOT NULL,
                IndustryID TEXT NOT NULL,
                DonationAmount REAL NOT NULL,
                FOREIGN KEY (LegislatorID) REFERENCES Legislators (LegislatorID),
                FOREIGN KEY (IndustryID) REFERENCES Industries (ID),
                PRIMARY KEY (LegislatorID, IndustryID)
            ); 
        """
        try:
            c = self.conn.cursor()
            c.execute(create_last_hr_rollcall_for_year_sql)
            c.execute(create_hr_rollcalls_sql)
            c.execute(create_legislators_sql)
            c.execute(create_hr_votes_sql)
            c.execute(create_industries_sql)
            c.execute(create_bills_sql)
            c.execute(create_bill_industries_sql)
            c.execute(create_legislator_donors_sql)
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

    def get_last_hr_rollcall_id(self):
        """Retrieve the most recent roll call ID and the corresponding year."""
        sql = "SELECT Year, RollCallID FROM RecentRollCall ORDER BY Year DESC, RollCallID DESC LIMIT 1"
        try:
            c = self.conn.cursor()
            c.execute(sql)
            result = c.fetchone()
            return (result[1], result[0]) if result else (None, None)
        except sqlite3.Error as e:
            print(e)
        return (None, None)

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

    def add_rollcall_data(self, rollcall_id, year, action_datetime, question, bill_name, bill_datetime, amendment_name, bill_title):
        """Insert a roll call into the database."""

        self.add_bill(bill_name, bill_datetime, bill_title)

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

    def add_bill(self, bill_name, bill_datetime, bill_title):
        """Insert a bill into the database."""
        sql = """ 
            INSERT INTO Bills(BillName, BillDateTime, BillTitle)
            VALUES(?, ?, ?)
            ON CONFLICT(BillName, BillDateTime) DO UPDATE SET BillTitle = excluded.BillTitle; 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (bill_name, bill_datetime, bill_title))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def add_bill_industry(self, bill_name, industry_id):
        """Insert a bill-industry pair into the database."""
        sql = """ 
            INSERT INTO BillIndustries(BillName, IndustryID)
            VALUES(?, ?)
            ON CONFLICT(BillName, IndustryID) DO NOTHING; 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (bill_name, industry_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def get_rollcall_data(self, rollcall_id, year):
        """Retrieve all meta data for roll call as well as each vote and pack it up into a dictionary"""
        rollcall_data = {}
        
        # Get roll call meta data
        rollcall_sql = """
            SELECT rc.*, b.BillTitle
            FROM RollCalls rc
            JOIN Bills b ON rc.BillName = b.BillName AND rc.BillDateTime = b.BillDateTime
            WHERE rc.RollCallID = ? AND rc.Year = ?
        """
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
                rollcall_data['BillTitle'] = rollcall_meta[7]
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
            rollcall_data['Votes'] = [{'LegislatorID': vote[0], 'Vote': vote[1]} for vote in votes]
        except sqlite3.Error as e:
            print(e)
            return None

        # Add legislator's name, state, and party to each vote
        for vote in rollcall_data['Votes']:
            legislator_sql = "SELECT * FROM Legislators WHERE LegislatorID = ?"
            try:
                c.execute(legislator_sql, (vote['LegislatorID'],))
                legislator = c.fetchone()
                vote['Name'] = legislator[1]
                vote['State'] = legislator[2]
                vote['Party'] = legislator[3]
            except sqlite3.Error as e:
                print(e)
                return None

        # Format ActionDateTime in the following format: YYYY-MM-DDTHH:MM:SSZ
        rollcall_data['ActionDateTime'] = rollcall_data['ActionDateTime'].replace(" ", "T") + "Z"

        # Sort votes by state in alphabetical order
        rollcall_data['Votes'] = sorted(rollcall_data['Votes'], key=lambda x: x['State'])

        return rollcall_data

    def add_legislator(self, legislator_id, name, state, party):
        """Insert a legislator into the database."""
        # Return if the legislator already exists
        if self.legislator_exists(legislator_id):
            return

        sql = """ 
            INSERT INTO Legislators(LegislatorID, Name, State, Party)
            VALUES(?, ?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (legislator_id, name, state, party))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def legislator_exists(self, legislator_id):
        """Check if a legislator exists in the database."""
        sql = "SELECT * FROM Legislators WHERE LegislatorID = ?"
        try:
            c = self.conn.cursor()
            c.execute(sql, (legislator_id,))
            return c.fetchone() is not None
        except sqlite3.Error as e:
            print(e)
        return False

    def vote_exists(self, action_datetime, legislator_id):
        """Check if a vote exists in the database."""
        sql = "SELECT * FROM Votes WHERE ActionDateTime = ? AND LegislatorID = ?"
        try:
            c = self.conn.cursor()
            c.execute(sql, (action_datetime, legislator_id))
            return c.fetchone() is not None
        except sqlite3.Error as e:
            print(e)
        return False

    def add_vote(self, action_datetime, legislator_id, vote):
        if self.vote_exists(action_datetime, legislator_id):
            return

        """Insert a vote into the database."""
        sql = """ 
            INSERT INTO Votes(ActionDateTime, LegislatorID, Vote)
            VALUES(?, ?, ?); 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (action_datetime, legislator_id, vote))
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
            previous_rollcall_data['Votes'] = [{'LegislatorID': vote[0], 'Vote': vote[1]} for vote in votes]

            for vote in previous_rollcall_data['Votes']:
                legislator_sql = "SELECT * FROM Legislators WHERE LegislatorID = ?"
                c.execute(legislator_sql, (vote['LegislatorID'],))
                legislator = c.fetchone()
                vote['Name'] = legislator[1]
                vote['State'] = legislator[2]
                vote['Party'] = legislator[3]

            previous_rollcall_data['ActionDateTime'] = previous_rollcall_data['ActionDateTime'].replace(" ", "T") + "Z"
            previous_rollcall_data['Votes'] = sorted(previous_rollcall_data['Votes'], key=lambda x: x['State'])

            return previous_rollcall_data
        except sqlite3.Error as e:
            print(e)
            return None

    def add_industry(self, id, description):
        """Insert an industry into the database."""
        sql = """ 
            INSERT INTO Industries(ID, Description)
            VALUES(?, ?)
            ON CONFLICT(ID) DO UPDATE SET Description = excluded.Description; 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (id, description))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def get_all_industries(self):
        """Retrieve all industries from the Industries table."""
        sql = "SELECT ID, Description FROM Industries"
        try:
            c = self.conn.cursor()
            c.execute(sql)
            industries = {row[0]: row[1] for row in c.fetchall()}
            return industries
        except sqlite3.Error as e:
            print(e)
            return []

    def add_legislator_industry(self, legislator_id, industry_id, donation_amount):
        """Insert a legislator-industry pair into the database."""
        sql = """ 
            INSERT INTO LegislatorIndustries(LegislatorID, IndustryID, DonationAmount)
            VALUES(?, ?, ?)
            ON CONFLICT(LegislatorID, IndustryID) DO UPDATE SET DonationAmount = excluded.DonationAmount; 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (legislator_id, industry_id, donation_amount))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def get_legislator_id(self, last_name, state_code):
        """Retrieve the legislator ID based on last name and state code."""
        sql = """
            SELECT LegislatorID
            FROM Legislators
            WHERE LOWER(Name) LIKE LOWER(?) AND LOWER(State) = LOWER(?)
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (f"%{last_name}%", state_code))
            result = c.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(e)
            return None

    def get_top_donors(self, legislator_id):
        """Retrieve the top industry donors for a legislator."""
        sql = """
            SELECT i.Description, li.DonationAmount
            FROM LegislatorIndustries li
            JOIN Industries i ON li.IndustryID = i.ID
            WHERE li.LegislatorID = ?
            ORDER BY li.DonationAmount DESC
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (legislator_id,))
            return [{'Description': row[0], 'DonationAmount': row[1]} for row in c.fetchall()]
        except sqlite3.Error as e:
            print(e)
            return []

    def get_related_bills(self, legislator_id):
        """Retrieve related bills for a legislator based on industry donations."""
        sql = """
            SELECT BillName
            FROM BillIndustries
            WHERE IndustryID IN (SELECT IndustryID FROM LegislatorIndustries WHERE LegislatorID = ?)
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (legislator_id,))
            return c.fetchall()
        except sqlite3.Error as e:
            print(e)
            return []

    def get_legislator_details(self, legislator_id):
        """Retrieve the details of a legislator based on their ID."""
        sql = """
            SELECT Name, State, Party
            FROM Legislators
            WHERE LegislatorID = ?
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (legislator_id,))
            result = c.fetchone()
            if result:
                return {
                    'last_name': result[0],
                    'state_code': result[1],
                    'party': result[2]
                }
            return None
        except sqlite3.Error as e:
            print(e)
            return None

    def get_related_rollcall_votes(self, legislator_id):
        """Retrieve all roll call votes for bills that are related to at least one of the legislator's donors."""
        sql = """
            SELECT rc.BillName, rc.BillDateTime, rc.RollCallID, rc.Year, v.Vote, rc.Question, GROUP_CONCAT(i.Description), b.BillTitle
            FROM RollCalls rc
            JOIN Votes v ON rc.ActionDateTime = v.ActionDateTime
            JOIN BillIndustries bi ON rc.BillName = bi.BillName
            JOIN Industries i ON bi.IndustryID = i.ID
            JOIN Bills b ON rc.BillName = b.BillName AND rc.BillDateTime = b.BillDateTime
            WHERE bi.IndustryID IN (
                SELECT IndustryID FROM LegislatorIndustries WHERE LegislatorID = ?
            )
            AND v.LegislatorID = ?
            GROUP BY rc.BillName, rc.BillDateTime, rc.RollCallID, rc.Year, v.Vote, rc.Question, b.BillTitle
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (legislator_id, legislator_id))
            return [{'BillName': row[0], 'BillDateTime': row[1], 'RollCallID': row[2], 'Year': row[3], 'Vote': row[4], 'Question': row[5], 'RelatedIndustries': row[6].split(','), 'BillTitle': row[7]} for row in c.fetchall()]
        except sqlite3.Error as e:
            print(e)
            return []