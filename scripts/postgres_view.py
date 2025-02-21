import pandas as pd
import psycopg

# Connect to PostgreSQL
conn = psycopg.connect(
    dbname="cia", user="testusr", password="testpwd", host="localhost", port=5432
)

# Load table into DataFrame
df = pd.read_sql("SELECT * FROM articles", conn)
df.to_csv("articles.csv", index=False)

# Close the connection
conn.close()
