[
  { 
    "feature": "Checkout",
    "use_case": "Finish purchase process",
    "initiatior": "Character does not have CharacterTrait with type= 'behavior", // key identificator for the agent to decide whether to suggest
    "suggestion_label": "Proceed to checkout", // Label for the suggestion button
    "suggestion_text": "Ready to complete your purchase? Let's head to checkout!", // Text sent to the chatbot
    "be_function": "start_checkout", // Function to be called when the suggestion is clicked (optional)
    "fe_navigation": "center.actors.about", // Navigation path for the frontend (optional)
    "topic": "character", // Topic of the suggestion (e.g., character, story, dialogue, scene, plot, theme)
  }
]

// A. Feature dictionary for managing the app via chatbot
// 1. Character features: 
// Create a character (name, type, faction)
// Add character traits (personality, background, communication style, humor, behavior, knowledge)
// Create character relationship (type, description)
// Analyze missing features 
// Assign character to a faction
// 2. Story features:
// Create a story description (title, genre, theme)
// Create act description
// Evaluate act/story beats 
// Analyze missing features
// 3. Dialogue features:
// Create dialogue (characters, setting, tone)
// Create dialogue structure (introduction, conflict, resolution)
// Create dialogue analysis (character development, plot progression, emotional impact)
// Evaluate dialogue structure and suggest improvements
// 4. Scene features:
// Create scene description (setting, characters, conflict)
// Create scene structure (introduction, rising action, climax, falling action, resolution)
// Create scene analysis (character development, plot progression, emotional impact)
// Evaluate scene structure and suggest improvements
// 5. Plot features:
// Create plot outline (beginning, middle, end)
// Create plot structure (exposition, rising action, climax, falling action, resolution)
// Create plot analysis (character development, plot progression, emotional impact)
// Evaluate plot structure and suggest improvements
// 6. Theme features:
// Create theme description (central idea, message)
// Create theme structure (introduction, development, conclusion)
// Create theme analysis (character development, plot progression, emotional impact)
// Evaluate theme structure and suggest improvements
// 7. Character development features:
// Create character arc (introduction, development, conclusion)
// Create character development structure (introduction, development, conclusion)
// 8. Create a faction (name, description)

// B. Notification system with SSE