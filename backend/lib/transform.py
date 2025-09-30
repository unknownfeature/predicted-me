import uuid
from datetime import datetime
from typing import Dict, Any, List, TypeVar, Type
from enum import Enum
from sqlalchemy.orm import RelationshipProperty, class_mapper
from sqlalchemy.engine import Row

from backend.lib.db import Note

#  todo review what AI generated here
T = TypeVar('T')


def serialize_value(value: Any) -> Any:
    """Converts special types (UUID, datetime, Enum) into serializable types."""
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        # Return time in ISO 8601 format (preferred for APIs)
        return value.isoformat()
    if isinstance(value, Enum):
        # Return the string value of the Enum member
        return value.value
    # Add other special types here if needed (e.g., Decimal/Numeric to float)
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value

    # Handle SQLAlchemy Numeric types explicitly
    if isinstance(value, (float, int)):
        return value

    # If it's a list/tuple, serialize its contents
    if isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]

    return value


def to_dict(instance: T, visited_entities: set = None) -> Dict[str, Any]:
    """
    Converts a single SQLAlchemy ORM instance into a dictionary, handling
    relationships and preventing recursive loops.

    Args:
        instance: The ORM object (User, Note, Metrics, etc.).
        visited_entities: Set of objects already processed in the current call stack.

    Returns:
        A dictionary representation of the instance.
    """
    if visited_entities is None:
        visited_entities = set()

    # Check for recursion
    if instance in visited_entities:
        return {'id': instance.id, 'status': 'recursive_link_omitted'}

    visited_entities.add(instance)

    data = {}
    mapper = class_mapper(instance.__class__)

    # 1. Handle regular columns and scalar attributes
    for column in mapper.columns:
        attr_name = column.key
        data[attr_name] = serialize_value(getattr(instance, attr_name))

    # 2. Handle relationships
    for relationship_prop in mapper.relationships:
        attr_name = relationship_prop.key
        value = getattr(instance, attr_name)

        # Check if relationship should be omitted (e.g., backref to parent)
        if relationship_prop.direction.name == 'ONETOMANY' or relationship_prop.direction.name == 'MANYTOMANY':
            if value is not None:
                # Handle lists of related objects
                data[attr_name] = [
                    to_dict(item, visited_entities.copy()) for item in value
                ]
            else:
                data[attr_name] = []

        elif relationship_prop.direction.name == 'MANYTOONE' and value is not None:
            # Handle single related object (many-to-one, like note.user)
            data[attr_name] = to_dict(value, visited_entities.copy())

    return data


def from_dict(model_class: Type[T], data: Dict[str, Any]) -> T:

    if not data:
        return None

    # Filter out keys that are not direct column attributes of the model
    # This prevents errors from trying to set relationship attributes or extra keys.
    column_names = {c.key for c in class_mapper(model_class).columns}

    filtered_data = {}
    for key, value in data.items():
        if key in column_names:
            filtered_data[key] = serialize_value(value)

    return model_class(**filtered_data)


# ----------------------------------------------------------------------
# Specific Transformers (Optional but useful for custom data cleansing/validation)
# ----------------------------------------------------------------------

def user_to_dict(user_instance):
    """Converts User instance, omitting circular relationships like child_users."""
    # We explicitly omit child_users to prevent a large, unneeded recursive tree
    # and parent_user to keep the structure flat.
    data = to_dict(user_instance)

    del data['child_users']
    del data['parent_user']
    del data['parent_user_id']

    return data


def note_from_dict(data: Dict[str, Any]) -> "Note":
    return from_dict(Note, data)


# --- Example Usage (Conceptual) ---
"""
# 1. Convert ORM object to dictionary:
note_dict = to_dict(note_instance)

# 2. Convert dictionary to ORM object (for POST):
new_user_instance = from_dict(User, {'name': 'Alice', 'external_id': 'abc...'})
"""