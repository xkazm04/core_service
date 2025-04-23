default_factions = [
    {
        "name": "Jedi order",
        "description": "The Jedi Order is a monastic, spiritual, and academic organization of Force-sensitive individuals known as Jedi. They are guardians of peace and justice in the galaxy, serving as diplomats and warriors.",
        "color": "#00FF00",
        "image_url": "https://example.com/jedi_order.png"
    },
    {
        "name": "Sith order",
        "description": "The Sith Order is a sect of Force-sensitive individuals who embrace the dark side of the Force. They are often in conflict with the Jedi and seek power and domination.",
        "color": "#FF0000",
        "image_url": "https://example.com/sith_order.png"
    },
    {
        "name": "Galactic Empire",
        "description": "The Galactic Empire is a totalitarian regime that rules the galaxy with an iron fist. It is known for its military might and oppressive policies.",
        "color": "#000000",
        "image_url": "https://example.com/galactic_empire.png"
    },
    {
        "name": "Rebel Alliance",
        "description": "The Rebel Alliance is a coalition of various groups and individuals who oppose the Galactic Empire. They fight for freedom and justice in the galaxy.",
        "color": "#FF00FF",
        "image_url": "https://example.com/rebel_alliance.png"
    },
    {
        "name": "Bounty Hunters Guild",
        "description": "The Bounty Hunters Guild is an organization of bounty hunters who work independently or in teams to capture targets for a fee. They operate outside the law and often have their own code of conduct.",
        "color": "#FFFF00",
        "image_url": "https://example.com/bounty_hunters_guild.png"
    }
]

default_faction_relationships = [
    {
        "faction_a_id": "1",
        "faction_b_id": "2",
        "relationship_type": "rivalry",
        "event": "The Jedi and Sith have been in conflict for centuries, with each side seeking to eliminate the other.",
    },
    {
        "relationship_type": "alliance",
        "event": "The Rebel Alliance has formed a temporary alliance with the Galactic Empire to combat a common threat.",
    },
    {
        "faction_a_id": "5",
        "faction_b_id": "1",
        "relationship_type": "neutral",
        "event": "The Bounty Hunters Guild has no formal allegiance to the Jedi Order but occasionally works with them.",
    },
    {
        "faction_a_id": "2",
        "faction_b_id": "3",
        "relationship_type": "rivalry",
        "event": "The Sith Order seeks to undermine the Galactic Empire from within.",
    },
    {
        "faction_a_id": "4",
        "faction_b_id": "5",
        "relationship_type": "neutral",
        "event": "The Rebel Alliance occasionally hires bounty hunters for special missions.",
    }
]