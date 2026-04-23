from sqlalchemy import create_engine, inspect

engine = create_engine("postgresql://postgres:C%40rden4s2k24@localhost/schedule_db")
inspector = inspect(engine)
columns = inspector.get_columns("rpt_planilla")
for column in columns:
    print(column["name"])
