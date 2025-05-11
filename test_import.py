# Simple test to check if personalized-shopping module can be imported without torch
try:
    import personalized_shopping

    print("SUCCESS: personalized_shopping module imported successfully")
except Exception as e:
    print(f"ERROR: {e}")
