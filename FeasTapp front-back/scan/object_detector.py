from ultralytics import YOLO
from flask import render_template, request, Response, Flask, send_from_directory, url_for
from waitress import serve
from PIL import Image
import json
import firebase_admin
from firebase_admin import credentials
from flask_restful import Resource, Api
import requests

cred = credentials.Certificate("feastapp-c4d79-firebase-adminsdk-wygrr-5dee5a902c.json")
firebase_admin.initialize_app(cred)


app = Flask(__name__, static_folder='static')
api = Api(app)

# Sample dish recommendation function
def recommend_dish(ingredient):
    # This is a placeholder, you can replace it with your actual recommendation logic
    dishes = {
        "tomato": "Caprese Salad",
        "apple": "Apple Pie",
        "banana": "Banana Bread",
        "carrot": "Carrot Soup",
        "eggplant": "Eggplant Parmesan",
        "lettuce": "Caesar Salad",
        "onion": "Adobo",
        "chicken": "Chicken Adobo"
    }
    return dishes.get(ingredient, "Unknown Dish")

@app.route("/")
def root():
    return render_template("scan.html")

@app.route("/chatbot")
def chatbot():
    # Serves the chatbot.html from the chatbot folder inside templates directory.
    return render_template("chatbot/chatbot.html")

@app.route("/main")
def main():
    # Serves the main.html from the main folder inside templates directory.
    return render_template("main/main.html")

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


@app.route("/detect", methods=["POST"])
def detect():
    buf = request.files["image_file"]
    boxes = detect_objects_on_image(Image.open(buf.stream))
    return Response(
        json.dumps(boxes),
        mimetype='application/json'
    )

def detect_objects_on_image(buf):
    model = YOLO("best.pt")
    results = model.predict(buf)
    result = results[0]
    output = []
    for box in result.boxes:
        x1, y1, x2, y2 = [round(x) for x in box.xyxy[0].tolist()]
        class_id = box.cls[0].item()
        prob = round(box.conf[0].item(), 2)
        ingredient = result.names[class_id]
        dish = recommend_dish(ingredient)
        output.append({
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "ingredient": ingredient, "probability": prob, "dish": dish
        })
    # Ensure only ingredient names are sent
    ingredients_list = [item['ingredient'] for item in output]
    send_ingredients_to_chatbot(ingredients_list)
    return output


def send_ingredients_to_chatbot(ingredients):
    url = 'http://127.0.0.1:5000/receive_ingredients'  # Corrected URL with endpoint
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, json={'ingredients': ingredients}, headers=headers)
        if response.status_code == 200:
            print("Ingredients sent successfully:", response.json())  # Print response from chatbot
        else:
            print("Failed to send ingredients, status code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Failed to connect to chatbot server:", e)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True, use_reloader=False)

