
import json

# at the top of app.py
import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -*- coding: utf-8 -*-
# Import necessary Python libraries
from flask import Flask, request, jsonify  # Flask is used to create the web app
from flask_cors import CORS  # import CORS here
from flask_sqlalchemy import SQLAlchemy
import os  # Used to access environment variables like your API key


# Create a Flask application
app = Flask(__name__)
CORS(app)  

# A database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://admin_homerecipe:Juneishere27!@home-recipe-db.ce94goyw2ngg.us-east-1.rds.amazonaws.com:5432/homerecipe?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

user_ingredients = db.Table('user_ingredients', 
	db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
	db.Column('ingredient_id', db.Integer, db.ForeignKey('ingredient.id'), primary_key=True)
)

# User table
class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True, nullable=False)
	ingredients = db.relationship('Ingredient', secondary=user_ingredients, backref=db.backref('users', lazy='dynamic'), lazy='dynamic')

	def __repr__(self):
		return f'<User {self.username}>'

#Ingredients table
class Ingredient(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), unique=True, nullable=False)

	def __repr__(self):
		return f'<Ingredient {self.name}>'

from datetime import datetime

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Recipe {self.title}>'

@app.route("/", methods=["GET"])
def health():
    return {"status": "ok", "service": "flask-api"}, 200


# Define the signup route (used to create a user and store ingredients)
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    ingredient_names = data.get('ingredients', [])

    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    if not isinstance(ingredient_names, list) or not ingredient_names:
        return jsonify({'error': 'A non-empty list of ingredients is required'}), 400

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400 

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409

    user = User(username=username)
    db.session.add(user)

    for name in ingredient_names:
        ingredient = Ingredient.query.filter_by(name=name).first()
        if not ingredient:
            ingredient = Ingredient(name=name)
            db.session.add(ingredient)
        user.ingredients.append(ingredient)

    db.session.commit()

    return jsonify({'message': f'User {username} created with {len(ingredient_names)} ingredients'}), 201


#Define the /suggest-ingredients route in Flask
@app.route("/suggest-ingredients", methods=["GET"])
def suggest_ingredients():
    query = request.args.get("q", "").lower()
    mock_data = {
        "vegetables": ["tomato", "carrot", "lettuce"],
        "fruits": ["apple", "banana", "mango"],
        "proteins": ["chicken", "beef", "tofu"],
    }

    results = {}
    for category, items in mock_data.items():
        results[category] = [item for item in items if query in item.lower()]

    return jsonify(results)


	# For each ingredient name:
    for name in ingredient_names:
        ingredient = Ingredient.query.filter_by(name=name).first()
        if not ingredient:
            ingredient = Ingredient(name=name)
            db.session.add(ingredient)
        user.ingredients.append(ingredient)

    db.session.commit()

    return jsonify({'message': f'User {username} created with ingredients'}), 201

@app.route('/user/<username>/ingredients', methods=['GET'])
def get_user_ingredients(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    ingredient_names = [ingredient.name for ingredient in user.ingredients]
    return jsonify({"ingredients": ingredient_names})

@app.route('/user/<username>', methods=['GET'])
def get_user_profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    ingredients = [i.name for i in user.ingredients]
    
    # Retrieve user's recipes (we’ll build Recipe model next)
    user_recipes = Recipe.query.filter_by(user_id=user.id).order_by(Recipe.timestamp.desc()).limit(3).all()
    recipes = [{'title': r.title, 'content': r.content} for r in user_recipes]

    return jsonify({
        'username': user.username,
        'ingredients': ingredients,
        'recipes': recipes
    })

import openai  # Make sure to install openai via pip
openai.api_key = os.getenv('OPENAI_API_KEY')  # Secure way to store API key


@app.route('/generate-recipe/<username>', methods=['GET'])
def generate_recipe_for_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    ingredients = [ing.name for ing in user.ingredients]
    if not ingredients:
        return jsonify({'error': 'No ingredients found for user'}), 400

    # We’ll ask for strict JSON:
    system_msg = (
        "You are a helpful home cooking assistant. "
        "Respond ONLY with valid JSON that matches the schema. No markdown."
    )
    user_msg = {
        "task": "create_recipes",
        "constraints": {
            "recipes_total": 3,
            "use_only_user_ingredients_for_first_n": 2,
            "allow_one_extra_pantry_item_for_last": True,
            "allowed_pantry_items_example": ["salt", "pepper", "onion", "garlic", "olive oil", "lemon"]
        },
        "user_ingredients": ingredients,
        "output_schema": {
            "recipes": [
                {
                    "title": "string",
                    "ingredients": ["string"],
                    "steps": ["string"]
                }
            ]
        }
    }

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",  # switch to another available chat model if needed
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": json.dumps(user_msg)}
            ],
            temperature=0.7,
            max_tokens=900,
            response_format={"type": "json_object"}  # enforce JSON-only response
        )

        raw = resp.choices[0].message.content
        data = json.loads(raw)  # -> dict with {"recipes":[...]}
        recipes = data.get("recipes", [])

        # Normalize & store
        out = []
        for idx, r in enumerate(recipes[:3], start=1):
            title = (r.get("title") or f"Recipe {idx}").strip()
            ings = r.get("ingredients") or []
            steps = r.get("steps") or []

            # Prepare a readable body for DB
            body = ""
            if ings:
                body += "Ingredients:\n" + "\n".join(f"- {i}" for i in ings) + "\n\n"
            if steps:
                body += "Steps:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))

            recipe_row = Recipe(title=title, content=body.strip(), user_id=user.id)
            db.session.add(recipe_row)
            out.append({"title": title, "ingredients": ings, "steps": steps})

        db.session.commit()
        return jsonify({"recipes": out}), 200

    except Exception as e:
        # Fallback: return raw text for debugging
        return jsonify({"error": str(e)}), 500




# Start the Flask server
if __name__ == '__main__':
    app.run(debug=True)
