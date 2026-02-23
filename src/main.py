from brightspace_parser import parse_to_duedate

due_dates = parse_to_duedate()

for due_date in due_dates:
    print(f"{due_date.due_date} | {due_date.course} | {due_date.title} | {due_date.type}")