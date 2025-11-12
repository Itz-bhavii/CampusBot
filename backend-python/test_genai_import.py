import sys
import os

try:
    import google.generativeai
    print("Successfully imported google.generativeai")
except ImportError as e:
    print(f"ImportError: {e}")
    print("sys.path:", sys.path)
    print("PYTHONPATH:", os.environ.get('PYTHONPATH'))
except Exception as e:
    print(f"An unexpected error occurred: {e}")
