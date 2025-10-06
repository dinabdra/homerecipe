import config from './config';
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import './App.css';

export default function App() {
  const [ingredientInput, setIngredientInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [username, setUsername] = useState('');
  const [addedIngredients, setAddedIngredients] = useState([]);
  const backgroundImages = [
    '/food/banana.jpg',
    '/food/burger.jpg',
    '/food/faces.jpg',
  ];

  const [bgIndex, setBgIndex] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setBgIndex((i) => (i + 1) % backgroundImages.length);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (ingredientInput.length < 1) {
        setSuggestions([]);
        return;
      }
      try {
        const res = await fetch(
          `${config.API_BASE_URL}/suggest-ingredients?q=${ingredientInput}`
        );
        const data = await res.json();
        const flatList = Object.entries(data)
          .flatMap(([category, items]) =>
            items.map((item) => `${item} (${category})`)
          );
        setSuggestions(flatList);
      } catch (err) {
        console.error('Suggestion fetch failed', err);
      }
    };
    const timeout = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(timeout);
  }, [ingredientInput]);

  const handleSubmit = async () => {
    const cleanIngredients = addedIngredients.map((ing) => ing.split(' (')[0]);
    const payload = {
      username,
      ingredients: cleanIngredients,
    };
    try {
      const res = await fetch(`${config.API_BASE_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      
      const data = await res.json();
      alert(data.message || 'Signup successful');
    } catch (error) {
      console.error('Signup error:', error);
    }
  };

  const handleAddIngredient = (ingredient) => {
    if (!addedIngredients.includes(ingredient)) {
      setAddedIngredients([...addedIngredients, ingredient]);
      setIngredientInput('');
      setSuggestions([]);
    }
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden">
      <motion.img
        key={bgIndex}
        src={backgroundImages[bgIndex]}
        initial={{ scale: 1 }}
        animate={{ scale: 1.3 }}
        transition={{ duration: 10, ease: 'easeInOut' }}
        className="absolute w-full h-full object-cover z-0"
      />
      <div className="absolute inset-0 bg-black bg-opacity-40 z-10 flex items-center justify-center">
        <div className="bg-white p-6 rounded-2xl shadow-xl w-full max-w-md z-20">
          <h1 className="text-2xl font-bold mb-4">Sign Up</h1>

        

          <input
            className="border p-2 w-full mb-4 rounded"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <div className="relative">
            <input
              className="border p-2 w-full mb-2 rounded"
              placeholder="Add Ingredient"
              value={ingredientInput}
              onChange={(e) => setIngredientInput(e.target.value)}
            />
            {suggestions.length > 0 && (
              <ul className="absolute bg-white border w-full rounded shadow z-30 max-h-48 overflow-y-auto">
                {suggestions.map((sugg, idx) => (
                  <li
                    key={idx}
                    className="p-2 hover:bg-gray-200 cursor-pointer"
                    onClick={() => handleAddIngredient(sugg)}
                  >
                    {sugg}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="flex flex-wrap gap-2 my-2">
            {addedIngredients.map((ing, idx) => (
              <span key={idx} className="bg-blue-100 px-2 py-1 rounded text-sm">
                {ing}
              </span>
            ))}
          </div>
          <button
            onClick={handleSubmit}
            className="bg-blue-600 text-white px-4 py-2 rounded mt-4 w-full"
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}
