common_item_schema = {
    "type": "object",
    "required": ["id", "type", "time"],
    "properties": {
        "id": {"type": "integer"},
        "type": {"type": "string", "enum": ["story", "comment", "job", "poll", "pollopt"]},
        "by": {"type": "string"},
        "time": {"type": "integer"},
        "text": {"type": "string"},
        "title": {"type": "string"},
        "url": {"type": "string"},
        "score": {"type": "integer"},
        "descendants": {"type": "integer"},
        "kids": {
            "type": "array",
            "items": {"type": "integer"}
        },
        "dead": {"type": "boolean"},
        "deleted": {"type": "boolean"},
        "parent": {"type": "integer"},
        "poll": {"type": "integer"},
        "parts": {
            "type": "array",
            "items": {"type": "integer"}
        }
    },
    "additionalProperties": True,
}

comment_schema = {
    "allOf": [
        common_item_schema,
        {
            "type": "object",
            "properties": {
                "type": {"const": "comment"},
                "parent": {"type": "integer"}
            },
            "required": ["parent"]
        }
    ]
}

story_schema = {
    "allOf": [
        common_item_schema,
        {
            "type": "object",
            "properties": {
                "type": {"const": "story"},
                "title": {"type": "string"},
                "score": {"type": "integer"}
            }
        }
    ]
}

job_schema = {
    "allOf": [
        common_item_schema,
        {"type": "object", "properties": {"type": {"const": "job"}}}
    ]
}

poll_schema = {
    "allOf": [
        common_item_schema,
        {"type": "object", "properties": {"type": {"const": "poll"}, "parts": {"type": "array"}}}
    ]
}

pollopt_schema = {
    "allOf": [
        common_item_schema,
        {"type": "object", "properties": {"type": {"const": "pollopt"}, "poll": {"type": "integer"}}}
    ]
}

user_schema = {
    "type": "object",
    "required": ["id", "created", "karma"],
    "additionalProperties": True,
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "created": {"type": "integer", "minimum": 0},
        "karma": {"type": "integer"},
        "about": {"type": "string"},
        "submitted": {"type": "array", "items": {"type": "integer"}},
    },
}
