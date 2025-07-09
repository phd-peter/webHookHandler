from app import app

# This file allows the application to be run with standard Flask commands
# and works with most deployment systems that look for main.py

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
