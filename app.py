from flask import Flask, render_template, request
import pickle
import numpy as np

app = Flask(__name__)

# Load model once
model = pickle.load(open("dreamdataset_model.pkl", "rb"))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get input values
        age = float(request.form['age'])
        gender = int(request.form['gender'])
        communication = int(request.form['communication'])
        interaction = int(request.form['interaction'])
        play = int(request.form['play'])
        stereotype = int(request.form['stereotype'])
        scq_score = float(request.form['scq_score'])

        # Arrange input
        features = np.array([[age, gender, communication, interaction, play, stereotype, scq_score]])

        # Predict
        prediction = model.predict(features)[0]

        return render_template('index.html', result=round(prediction, 2))

    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.run(debug=True)