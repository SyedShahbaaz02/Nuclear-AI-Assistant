import sys
import os

# Ensure the chat_service directory is in the Python path
# This allows us to import modules from the chat_service directory in our tests.
# Adjust the path as necessary based on your project structure.
chat_service_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'chat_service'))
print(f"Adding {chat_service_path} to sys.path")
sys.path.append(chat_service_path)
