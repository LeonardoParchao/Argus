import sqlite3
import uuid
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'osint.db')


def init_db() -> None:
    """Create tables if they don't exist."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create entities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            source TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create relationships table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            confidence INTEGER DEFAULT 50,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES entities(id),
            FOREIGN KEY (target_id) REFERENCES entities(id)
        )
    ''')
    
    # Create profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create profile_links table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile_links (
            id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles(id),
            FOREIGN KEY (entity_id) REFERENCES entities(id)
        )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_value ON entities(value)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profile_links_profile ON profile_links(profile_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_profile_links_entity ON profile_links(entity_id)')
    
    conn.commit()
    conn.close()


def upsert_entity(entity_type: str, value: str, source: Optional[str] = None) -> str:
    """Insert or ignore if exists, return ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if entity already exists
    cursor.execute('SELECT id FROM entities WHERE type = ? AND value = ?', (entity_type, value))
    existing = cursor.fetchone()
    
    if existing:
        entity_id = existing[0]
    else:
        entity_id = str(uuid.uuid4())
        cursor.execute(
            'INSERT INTO entities (id, type, value, source) VALUES (?, ?, ?, ?)',
            (entity_id, entity_type, value, source)
        )
        conn.commit()
    
    conn.close()
    return entity_id


def create_relationship(source_id: str, target_id: str, relation_type: str, confidence: int = 50) -> str:
    """Insert into relationships."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    relationship_id = str(uuid.uuid4())
    cursor.execute(
        'INSERT INTO relationships (id, source_id, target_id, relation_type, confidence) VALUES (?, ?, ?, ?, ?)',
        (relationship_id, source_id, target_id, relation_type, confidence)
    )
    conn.commit()
    conn.close()
    
    return relationship_id


def create_profile(name: str, notes: Optional[str] = None) -> str:
    """Create a profile and return profile_id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    profile_id = str(uuid.uuid4())
    cursor.execute(
        'INSERT INTO profiles (id, name, notes) VALUES (?, ?, ?)',
        (profile_id, name, notes)
    )
    conn.commit()
    conn.close()
    
    return profile_id


def link_entity_to_profile(profile_id: str, entity_id: str) -> str:
    """Link an entity to a profile."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    link_id = str(uuid.uuid4())
    cursor.execute(
        'INSERT INTO profile_links (id, profile_id, entity_id) VALUES (?, ?, ?)',
        (link_id, profile_id, entity_id)
    )
    conn.commit()
    conn.close()
    
    return link_id


def get_graph_data() -> Dict:
    """Query adjacency list and format into { nodes: [], edges: [] } for Cytoscape.js."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all entities as nodes
    cursor.execute('SELECT id, type, value, source FROM entities')
    nodes = []
    for row in cursor.fetchall():
        node_id, entity_type, value, source = row
        nodes.append({
            'data': {
                'id': node_id,
                'label': value,
                'type': entity_type,
                'source': source
            }
        })
    
    # Get all relationships as edges
    cursor.execute('SELECT id, source_id, target_id, relation_type, confidence FROM relationships')
    edges = []
    for row in cursor.fetchall():
        edge_id, source_id, target_id, relation_type, confidence = row
        edges.append({
            'data': {
                'id': edge_id,
                'source': source_id,
                'target': target_id,
                'label': relation_type,
                'confidence': confidence
            }
        })
    
    conn.close()
    
    return {
        'nodes': nodes,
        'edges': edges
    }


def get_entity_by_id(entity_id: str) -> Optional[Dict]:
    """Get entity details by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, type, value, source, created_at FROM entities WHERE id = ?', (entity_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'type': row[1],
            'value': row[2],
            'source': row[3],
            'created_at': row[4]
        }
    return None


def get_profiles() -> List[Dict]:
    """Get all profiles."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, notes, created_at FROM profiles ORDER BY created_at DESC')
    profiles = []
    for row in cursor.fetchall():
        profiles.append({
            'id': row[0],
            'name': row[1],
            'notes': row[2],
            'created_at': row[3]
        })
    
    conn.close()
    return profiles


def get_profile_entities(profile_id: str) -> List[Dict]:
    """Get all entities linked to a profile."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.id, e.type, e.value, e.source
        FROM entities e
        INNER JOIN profile_links pl ON e.id = pl.entity_id
        WHERE pl.profile_id = ?
    ''', (profile_id,))
    
    entities = []
    for row in cursor.fetchall():
        entities.append({
            'id': row[0],
            'type': row[1],
            'value': row[2],
            'source': row[3]
        })
    
    conn.close()
    return entities
