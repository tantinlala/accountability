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
        create_bill_updates_sql = """ 
            CREATE TABLE IF NOT EXISTS BillUpdates (
                BillID TEXT PRIMARY KEY,
                LastUpdated TIMESTAMP NOT NULL
            ); 
        """
        try:
            c = self.conn.cursor()
            c.execute(create_recent_roll_call_sql)
            c.execute(create_bill_updates_sql)
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

    def update_bill_last_updated(self, bill_id, last_updated):
        """Update the last updated timestamp for a given bill ID."""
        sql = """ 
            INSERT INTO BillUpdates(BillID, LastUpdated)
            VALUES(?, ?)
            ON CONFLICT(BillID) DO UPDATE SET LastUpdated = excluded.LastUpdated; 
        """
        try:
            c = self.conn.cursor()
            c.execute(sql, (bill_id, last_updated))
            self.conn.commit()
        except sqlite3.Error as e:
            print(e)

    def get_bill_last_updated(self, bill_id):
        """Retrieve the last updated timestamp for a given bill ID."""
        sql = "SELECT LastUpdated FROM BillUpdates WHERE BillID = ?"
        try:
            c = self.conn.cursor()
            c.execute(sql, (bill_id,))
            result = c.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(e)
        return None

# Example usage
if __name__ == "__main__":
    db = CongressDatabase()
    # Example operations...