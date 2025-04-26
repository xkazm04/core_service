interface Suggestion:
  feature: string // name of the feature to clearly identify it on the first sight
  use_case: string // description of the feature for better LLM understanding
  initiatior: string // condition for LLM based on which the feature is suggested
  suggested_label: string // button label displayed in chat window
  suggested_text: string // template for response format back to chatbot -- TBD není úplně domyšlený
  fe_function?: string // operation performed on fe side - customize suggestion
  be_function?: string // operation performed on be side - needs to be mapped in executor.py
  fe_navigation?: string // position of frontend page to navigate to - promyslet, initiate on click nebo automaticky - UI upravit
  topic: string // business context mapping
[
  { 
    "feature": "Create chracter",
    "use_case": "Create new character to the project. Required input: Name. Optional input: Faction, ...",
    "initiatior": "User requires in message to create a new character.", 
    "suggestion_label": "New character", 
    "suggestion_text": "Please create character with parameters: {{name}}, {{faction.id}}, {{type}}", 
    "fe_function": "character_create",
    "be_function": "character_create", 
    "fe_navigation": "center.characters", 
    "topic": "character"
  },
  {
    "feature": "Edit character",
    "use_case": "Edit character details",
    "initiator": "User requires in message to edit character details",
    "suggestion_label": "Edit character",
    "suggestion_text": "Please edit character with parameters: {{name}}, {{faction.id}}, {{type}}",
    "fe_function": "character_edit",
    "be_function": "character_edit",
    "fe_navigation": "center.characters",
    "topic": "character"
  }
  {
    "feature": "Edit character trait",
    "use_case": "Add detailed description about the character",
    "initiator": "Add or edit character trait for detailed description about following sections: Behavior, Humor, Speech, Knowledge",
    "suggestion_label": "Add trait"
    "suggestion_text": "Please add CharacterTrait with parameters: {{type}}, {{description}}",
    "fe_function": "trait_add",
    "be_function": "trait_add",
    "topic": "character" 
  },
  {
    "feature": "Create character relationship",
    "use_case": "Add relationship event between two character",
    "initiatior": "User request or missing relationship between two characters",
    "suggestion_label": "Add relationship",
    "suggestion_text": "Please add CharacterRelationship with parameters: "// TBD poodle modelu,
    "fe_function": "char_relationship_add",
    "be_function": "char_relationship_add",
    "topic": "character"
  },
  {
    "feature": "Edit character relationship" 
    "use_case": "Add detailed description about the character relationship",
    "initiator": "Add or edit character relationship for detailed description about following sections: Type, Description",
    "suggestion_label": "Add relationship",
    "suggestion_text": "Please add CharacterRelationship with parameters: {{type}}, {{description}}",
    "fe_function": "char_relationship_add",
    "be_function": "char_relationship_add",
    "topic": "character"
  },
  {
    "feature": "Analyze character gaps",
    "use_case": "Find missing character traits, relationships, ideas for improvements",
    "initiator": "User requests or missing character traits, relationships, ideas for improvements",
    "suggestion_label": "Analyze character gaps",
    "suggestion_text": "Please analyze character gaps with parameters: {{character.id}}",
    "fe_function": "char_gaps_analyze",
    "be_function": "char_gaps_analyze",
    "topic": "character"
  },
  {
    "feature": "Assign faction",
    "use_case": "Assign character to a faction",
    "initiator": "User requests or missing character traits, relationships, ideas for improvements",
    "suggestion_label": "Assign faction",
    "suggestion_text": "Please assign character to faction with parameters: {{faction.id}}",
    "fe_function": "char_assign_faction",
    "be_function": "char_assign_faction",
    "topic": "character"
  },
]



// A. Feature dictionary for managing the app via chatbot
// 1. Character features - Done - now needed to test.
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