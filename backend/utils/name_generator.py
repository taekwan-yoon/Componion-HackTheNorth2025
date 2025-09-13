import random

ADJECTIVES = [
    'Brave', 'Swift', 'Clever', 'Mighty', 'Gentle', 'Bold', 'Wise', 'Noble',
    'Fierce', 'Quick', 'Strong', 'Bright', 'Silent', 'Proud', 'Wild', 'Free',
    'Ancient', 'Cosmic', 'Electric', 'Golden', 'Silver', 'Crimson', 'Azure',
    'Emerald', 'Violet', 'Radiant', 'Mystical', 'Legendary', 'Epic', 'Divine'
]

ANIMALS = [
    'Lion', 'Eagle', 'Fox', 'Wolf', 'Bear', 'Hawk', 'Tiger', 'Panther',
    'Dragon', 'Phoenix', 'Falcon', 'Shark', 'Leopard', 'Cheetah', 'Raven',
    'Owl', 'Deer', 'Buffalo', 'Stallion', 'Jaguar', 'Lynx', 'Cobra',
    'Viper', 'Rhino', 'Elephant', 'Whale', 'Dolphin', 'Octopus', 'Kraken',
    'Griffin', 'Pegasus', 'Unicorn', 'Sphinx', 'Chimera', 'Hydra'
]

def generate_random_name():
    """Generate a random name using Adjective + Animal format"""
    adjective = random.choice(ADJECTIVES)
    animal = random.choice(ANIMALS)
    return f"{adjective} {animal}"

def generate_user_id():
    """Generate a unique user ID"""
    import uuid
    return str(uuid.uuid4())[:8]  # Short UUID for user ID
