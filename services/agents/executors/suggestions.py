
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
        "doublecheck": True
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
        "doublecheck": True
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
        "doublecheck": True
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
        "doublecheck": True
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
        "doublecheck": True
    }
]
