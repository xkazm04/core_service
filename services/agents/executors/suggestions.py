
initial_suggesions = [
    { 
        "feature": "Develope character",
        "use_case": "Predecessor to build the character look, personality, way it behaves and speaks.",
        "initiator": "User wonders what features can he do in the project.",
        "message": "Please provide me options from `initial` topic to start with.",
        "be_function": "initial_character",
        "fe_function": "initial_character",
        "fe_location": "center.char.list",
        "topic": "initial",
        "doublecheck": False
    },
    {
        "feature": "Write a story",
        "use_case": "Predecessor to build the story, plot, and dialog lines.",
        "initiator": "User wonders what features can he do in the project.",
        "message": "Please provide me options from `initial` topic to start with.",
        "be_function": "initial_story",
        "fe_function": "initial_story",
        "fe_location": "center.story",
        "topic": "initial",
        "doublecheck": False
    }
]

suggestion_data = [
    {
        "feature": "Select character",
        "use_case": "Select character to gather more details about.",
        "initiator": "User requires information about a character and we need to specify it to gather more details. Always suggest, if the character is not specified.",
        "message": "Character ID specified in the request params.",
        "fe_function": "character_select",
        "be_function": "character_select",
        "fe_location": "center.char.list",
        "topic": "character",
        "doublecheck": "true",
    },
    {
        "feature": "Create chracter",
        "use_case": "Create new character to the project.",
        "initiator": "User requires in message specifically to create a new character, or mentiones a character name not known to the project.",
        "message": "Character name and type specified in the request params.",
        "fe_function": "character_create",
        "be_function": "character_create",
        "fe_location": "center.char.list",
        "topic": "character",
        "doublecheck": "true",
        "kwargs_form": {
            "target_char_name": "input",
            "target_char_type": "character_type_select",
        }
    },
    {
        "feature": "Rename character",
        "use_case": "Change name of the existing character in project.",
        "initiator": "User requires in message to rename character",
        "message": "Character name specified in the request params.",
        "fe_function": "character_rename",
        "be_function": "character_rename",
        "fe_location": "center.char.list",
        "topic": "character",
        "doublecheck": "true",
        "kwargs_form": {
            "target_char_name": "input",
            "character_id": "character_select",
        }
    },
    {
        "feature": "Edit character trait",
        "use_case": "Add detailed description about the character",
        "initiator": "User wants to add or edit character trait for detailed description about following sections: Behavior, Humor, Speech, Knowledge",
        "message": "Section and description specified in the request params.",
        "fe_function": "trait_add",
        "be_function": "trait_add",
        "fe_location": "center.char.about",
        "topic": "character",
        "doublecheck": "true",
        "kwargs_form": {
            "trait_description": "textarea",
        }
    },
    {
        "feature": "Add relationship",
        "use_case": "Create relationship event between two characters.",
        "initiator": "User requires in message to create a relationship between two characters.",
        "message": "Character ID and relationship type specified in the request params.",
        "fe_function": "relationship_add",
        "be_function": "relationship_add",
        "fe_location": "center.char.rel",
        "topic": "character",
        "doublecheck": "true",
        "kwargs_form": {
            "secondary_character_id": "character_select",
            "relationship_type": "relationship_type_select",
            "relationship_description": "textarea",
        }
    },
    {
        "feature": "Create faction",
        "use_case": "Create new faction to the project.",
        "initiator": "User requires in message specifically to create a new faction, or mentiones a faction name not known to the project.",
        "message": "Faction name and description specified in the request params.",
        "fe_function": "faction_create",
        "be_function": "faction_create",
        "fe_location": "center.char.factions",
        "topic": "faction",
        "doublecheck": "true",
        "kwargs_form": {
            "faction_name": "input",
            "faction_description": "textarea",
        }
    },
    {
        "feature": "Rename faction",
        "use_case": "Change name of the existing faction in project.",
        "initiator": "User requires in message to rename faction",
        "message": "Faction name specified in the request params.",
        "fe_function": "faction_rename",
        "be_function": "faction_rename",
        "fe_location": "center.char.factions",
        "topic": "faction",
        "doublecheck": "true",
        "kwargs_form": {
            "faction_name": "input",
            "faction_id": "faction_select",
        }
    },
    # Story (Act, Beat, Scene)
    {
        "feature": "Act concept",
        "use_case": "Suggestion of creative idea to design story act based on available project information.",
        "initiator": "User requires specifically to design act concept, before manipulation in database.",
        "message": "Feedback provided in request kwargs",
        "fe_function": "act_concept",
        "fe_location": "center.story",
        "topic": "story",
        "doublecheck": "true",
        "kwargs_form": {
            "act_concept": "textarea",
            "act_id": "select",
        }
    },
    {
        "feature": "Create act",
        "use_case": "Create new act to the project.",
        "initiator": "User requires in message specifically to create a new act, or mentiones an act name not known to the project.",
        "message": "Act name and description specified in the request params.",
        "fe_function": "act_create",
        "be_function": "act_create",
        "fe_location": "center.story",
        "topic": "story",
        "doublecheck": "true",
        "kwargs_form": {
            "act_name": "input",
            "act_description": "textarea",
        }
    },
    {
        "feature": "Edit act description",
        "use_case": "Edit act description in the project.",
        "initiator": "User wants to redesign act storyline based on the description in request parameters",
        "message": "Act id and description specified in the request params.",
        "fe_function": "act_edit",
        "be_function": "act_edit",
        "fe_location": "center.story",
        "topic": "story",
        "doublecheck": "true",
        "kwargs_form": {
            "act_description": "textarea",
            "act_id": "act_select",
        }
    },
    {
        "feature": "Beat concept",
        "use_case": "Suggestion of creative idea to design story objective (beat) based on available project information.",
        "initiator": "User requires specifically to design beat concept, before manipulation in database.",
        "message": "Feedback provided in request kwargs",
        "fe_function": "beat_concept",
        "fe_location": "center.story.beats",
        "topic": "story",
        "doublecheck": "true",
        "kwargs_form": {
            "beat_concept": "textarea",
        },
    },
    {
        "feature": "Create beat",
        "use_case": "Create new beat to the project.",
        "initiator": "User requires in message specifically to create a new beat, or mentiones a beat name not known to the project.",
        "message": "Beat name and description specified in the request params.",
        "fe_function": "beat_create",
        "be_function": "beat_create",
        "fe_location": "center.story.beats",
        "topic": "story",
        "doublecheck": "true",
        "kwargs_form": {
            "beat_name": "input",
            "beat_description": "textarea",
        }
    },{
        "feature": "Edit beat",
        "use_case": "Edit beat description in the project.",
        "initiator": "User wants to redesign beat storyline based on the description in request parameters",
        "message": "Beat id and description specified in the request params.",
        "fe_function": "beat_edit",
        "be_function": "beat_edit",
        "fe_location": "center.story.beats",
        "topic": "story",
        "doublecheck": "true",
        "kwargs_form": {
            "beat_description": "textarea",
            "beat_id": "beat_select",
        }
    }
]
