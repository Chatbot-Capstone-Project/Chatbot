from flask import Flask, render_template, request, jsonify
from trained_model_file import generate_response

app = Flask(__name__)

# Placeholder for your machine learning model integration
def get_bot_response(user_input):
    # calling ML Model to process user_input
    #Assuming Model is saved in "generate_response" function in Modeling file
    response = generate_response(user_input)
    # Return the bot's response
    return response

# Define the main route
@app.route('/')
def index():
    return render_template('index.html')

# Define a route for processing user input
@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form['user_input']
    bot_response = get_bot_response(user_input)
    return jsonify({'bot_response': bot_response})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
