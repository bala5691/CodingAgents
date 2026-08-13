from graph import app


request = """
    Build a customer support dashboard.

    Requirements:
    - React frontend
    - ticket table
    - ticket detail panel
    - filtering
    - responsive design
    - modern enterprise UI
    """

result = app.invoke({ "request": request, "iteration": 0, "max_iterations": 3 })

print("STATUS:")
print(result["status"])

print("\nFINAL IMPLEMENTATION:")
print(result["final_output"])

print("\nVISUAL QA:")
print(result.get("visual_qa"))

print("\nLOCAL REVIEW:")
print(result.get("local_review"))

print("\nFRONTIER REVIEW:")
print(result.get("frontier_review"))