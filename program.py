# Ursina Engine: Minecraft-Style Voxel World
# This script creates a self-contained, procedurally generated world
# with block placing/destroying mechanics, optimized for 60 FPS.

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from perlin_noise import PerlinNoise
import random

# -----------------------------------------------------------------------------
# App & Window Initialization
# -----------------------------------------------------------------------------
app = Ursina(
    title='Voxel Engine (60 FPS Target)',
    borderless=False,
    fullscreen=False,
    vsync=False, # Vsync must be disabled to manually limit FPS
    development_mode=True
)

# Set a fixed 60 FPS limit. This is crucial for stable performance.
from panda3d.core import ClockObject
globalClock = ClockObject.getGlobalClock()
globalClock.setMode(ClockObject.MLimited)
globalClock.setFrameRate(60.0)

# --- Window and Sky Setup ---
window.fps_counter.enabled = True
window.exit_button.visible = False
window.cog_button.visible = False
Sky()

# -----------------------------------------------------------------------------
# Texture Loading & Block Type Definitions
# -----------------------------------------------------------------------------
# To create the "no files" vibe, we load one basic texture and tint it.
# This is very efficient and avoids dependency on external image assets.
block_texture = load_texture('assets/white_cube')

# A dictionary to define our block types. We can easily add more here.
BLOCK_TYPES = {
    'grass': {'color': color.rgb(34, 177, 76), 'texture': block_texture},
    'dirt': {'color': color.rgb(139, 69, 19), 'texture': block_texture},
    'stone': {'color': color.rgb(128, 128, 128), 'texture': block_texture},
    'bedrock': {'color': color.black, 'texture': block_texture},
    'wood': {'color': color.rgb(160, 82, 45), 'texture': block_texture}
}

# The block type the player is currently holding/placing
current_block_type = 'grass'

# -----------------------------------------------------------------------------
# Voxel (Cube) Class
# -----------------------------------------------------------------------------
# Each block in our world will be a 'Voxel' entity.
# We inherit from Button, which gives us built-in hovering and click detection.
class Voxel(Button):
    def __init__(self, block_type='grass', position=(0, 0, 0)):
        if block_type not in BLOCK_TYPES:
            raise ValueError(f"Unknown block type: {block_type}")

        super().__init__(
            parent=scene,
            model='assets/block', # A custom model with optimized UVs
            origin_y=0.5,
            position=position,
            color=BLOCK_TYPES[block_type]['color'],
            texture=BLOCK_TYPES[block_type]['texture'],
            highlight_color=color.lime, # Color when hovered
            scale=1.0
        )
        self.block_type = block_type

    # This function is automatically called by Ursina when a key is pressed.
    def input(self, key):
        if self.hovered:
            # --- Place a block ---
            # 'right mouse down' is for placing. mouse.normal gives the face clicked.
            if key == 'right mouse down':
                new_position = self.position + mouse.normal
                # Prevent placing blocks inside the player
                if not (new_position.x == round(player.x) and \
                        new_position.y == round(player.y) and \
                        new_position.z == round(player.z)):
                    Voxel(block_type=current_block_type, position=new_position)

            # --- Destroy a block ---
            # 'left mouse down' is for destroying.
            if key == 'left mouse down':
                # Bedrock is indestructible
                if self.block_type != 'bedrock':
                    destroy(self)

# -----------------------------------------------------------------------------
# World Generation
# -----------------------------------------------------------------------------
# Use Perlin Noise to create natural-looking, random terrain.
noise = PerlinNoise(octaves=3, seed=random.randint(1, 1000))
world_size = 24
world_height = 8

print("Generating world... This may take a moment.")
for z in range(world_size):
    for x in range(world_size):
        # Calculate height with noise
        y = noise([x * 0.03, z * 0.03])
        y = floor(y * world_height)

        # Create the terrain layers
        Voxel(block_type='grass', position=(x, y, z))
        Voxel(block_type='dirt', position=(x, y - 1, z))
        Voxel(block_type='dirt', position=(x, y - 2, z))
        
        # Fill everything below with stone
        for depth in range(int(y) - 3, -1, -1):
             Voxel(block_type='stone', position=(x, depth, z))
        
        # Add a bedrock layer at the bottom
        Voxel(block_type='bedrock', position=(x, -1, z))
print("World generation complete.")

# -----------------------------------------------------------------------------
# Player and UI
# -----------------------------------------------------------------------------
player = FirstPersonController(
    speed=7,
    gravity=0.8,
    jump_height=2,
    jump_duration=0.4,
    position=(world_size / 2, world_height + 5, world_size / 2), # Start above the world
    mouse_sensitivity=Vec2(100, 100)
)

# --- UI Text for instructions and block selection ---
instructions = Text(
    text="[WASD] Move | [Space] Jump | [Mouse] Look | [LMB] Destroy | [RMB] Place",
    position=window.top_left + (0.01, -0.01),
    scale=0.9,
    background=True
)
block_selection_text = Text(
    text="[1] Grass | [2] Dirt | [3] Stone | [4] Wood",
    position=window.top_left + (0.01, -0.05),
    scale=0.9,
    background=True
)
current_block_text = Text(
    text=f"Selected: {current_block_type.capitalize()}",
    origin=(0, -18),
    scale=1.2,
    background=True
)

# -----------------------------------------------------------------------------
# Global Input Handling
# -----------------------------------------------------------------------------
def input(key):
    global current_block_type
    
    # Block selection logic
    if key.isdigit() and int(key) in range(1, 5):
        block_map = {'1': 'grass', '2': 'dirt', '3': 'stone', '4': 'wood'}
        current_block_type = block_map[key]
        current_block_text.text = f"Selected: {current_block_type.capitalize()}"
        
    # Fall out of world reset
    if player.y < -10:
        player.position = (world_size / 2, world_height + 5, world_size / 2)

# -----------------------------------------------------------------------------
# Run the Application
# -----------------------------------------------------------------------------
app.run()
