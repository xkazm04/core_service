operations_list_all = """- character_create: Creates a new character (extract: target_char_name for the character's name, type if available - if not, use default value 'major')
- character_rename: Renames a character (extract: existing character reference, new name as target_char_name)
- trait_add: Adds a trait to a character (extract: trait type, trait description)
- relationship_add: Creates a relationship (extract: both character references, relationship type, description)
- act_create: Creates a new act (extract: act name, description)
- act_edit: Edits an existing act (extract: act reference, new description)
- beat_create: Creates a new beat (extract: beat name, description)
- beat_edit: Edits a beat (extract: beat reference, new description)
- scene_create: Creates a new scene (extract: scene_name, description). If description not provided, create engaging scene description based on the message context. If not act provided, use Act 1.
- faction_create: Creates a new faction (extract: faction name, description)
- faction_rename: Renames a faction (extract: faction reference, new name)
""" 

operations_list_char = """- character_create: Creates a new character (extract: target_char_name for the character's name, type if available - if not, use default value 'major')
- character_rename: Renames a character (extract: existing character reference, new name as target_char_name)
- trait_add: Adds a trait to a character (extract: trait type, trait description)
- relationship_add: Creates a relationship (extract: both character references, relationship type, description)
"""

operations_list_story = """- act_create: Creates a new act (extract: act name, description)
- act_edit: Edits an existing act (extract: act reference, new description)
- beat_create: Creates a new beat (extract: beat name, description)
- beat_edit: Edits a beat (extract: beat reference, new description)
- scene_create: Creates a new scene (extract: scene_name, description). If description not provided, create engaging scene description based on the message context. If not act provided, use Act 1.
"""