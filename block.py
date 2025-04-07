import pygame
import random
import os

from constants import BLACK, CELL_SIZE, GRID_SIZE

# Map color tuples to image filenames
COLOR_TO_IMAGE = {
    (255, 0, 0): "red.png",      # Red
    (0, 255, 0): "green.png",    # Green
    (0, 0, 255): "blue.png",     # Blue
    (255, 255, 0): "yellow.png", # Yellow
    (255, 0, 255): "purple.png", # Magenta/Purple
    (0, 255, 255): "blue.png",   # Cyan (using blue as fallback)
    (255, 128, 0): "orange.png", # Orange
    (128, 0, 255): "purple.png", # Purple
    None: "empty.png",           # Empty cell
}

# Block definitions - each block is defined as a list of (row, col) relative positions
BLOCK_TYPES = {
  "1x3": [(0, 0), (0, 1), (0, 2)],
  "1x4": [(0, 0), (0, 1), (0, 2), (0, 3)],
  "1x5": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)],
  "2x2": [(0, 0), (0, 1), (1, 0), (1, 1)],
  "2x3": [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],
  "3x3": [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)],
  "Z_shape_2x3": [(0, 0), (0, 1), (1, 1), (1, 2)],
  "L_shape_2x3": [(0, 0), (1, 0), (1, 1), (1, 2)],
  "L_shape_3x3": [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
  "T_shape_2x3": [(0, 1), (1, 0), (1, 1), (1, 2)]
}

# Load tile images
TILE_IMAGES = {}
def load_tile_images():
    """Load all tile images from the tiles directory."""
    tiles_dir = "tiles"
    if not os.path.exists(tiles_dir):
        print(f"Warning: Tiles directory '{tiles_dir}' not found")
        return False
        
    for color, filename in COLOR_TO_IMAGE.items():
        image_path = os.path.join(tiles_dir, filename)
        if os.path.exists(image_path):
            try:
                TILE_IMAGES[color] = pygame.image.load(image_path).convert_alpha()
                # Scale the image to match the cell size
                TILE_IMAGES[color] = pygame.transform.scale(TILE_IMAGES[color], (CELL_SIZE, CELL_SIZE))
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
        else:
            print(f"Warning: Image file {image_path} not found")
    
    return len(TILE_IMAGES) > 0

def rotate_block(block, times=1):
    """Rotate the block the given number of times."""
    result = block.copy()  # Start with a copy of the original block
    for _ in range(times):
      # Get the highest y coordinate
      max_row = max(pos[0] for pos in result)
      # Rotate coordinates: (r, c) -> (c, max_row - r)
      result = [(c, max_row - r) for r, c in result]
    return result

class Block:
  def __init__(self, block_type, orientation_index=0):
    self.type = block_type
    # If no orientation index is provided, randomize it.
    self.orientation_index = orientation_index if orientation_index is not None else random.randint(0, 3)
    # Get the block's positions for the current orientation.
    self.positions = rotate_block(BLOCK_TYPES[block_type], self.orientation_index)
    # Randomize the block's color, excluding None (empty tile)
    valid_colors = [color for color in COLOR_TO_IMAGE.keys() if color is not None]
    self.color = random.choice(valid_colors)
    # Screen position
    self.x = 0
    self.y = 0
    # Dragging state
    self.dragging = False
    self.drag_offset_x = 0
    self.drag_offset_y = 0
    
    # Calculate block dimensions
    self.width = max(col for _, col in self.positions) + 1
    self.height = max(row for row, _ in self.positions) + 1
    
    # Load tile images if not already loaded
    if not TILE_IMAGES:
        load_tile_images()
    
  def set_position(self, x, y):
    """Set the block's position on the screen."""
    self.x = x
    self.y = y
      
  def contains_point(self, x, y):
    """Check if the given point is inside the block."""
    # Convert screen coordinates to block-local coordinates
    local_x = x - self.x
    local_y = y - self.y
    
    # Check if the point is within the block's bounding box
    if (0 <= local_x < self.width * CELL_SIZE and 
        0 <= local_y < self.height * CELL_SIZE):
      # Convert to grid coordinates
      grid_x = local_x // CELL_SIZE
      grid_y = local_y // CELL_SIZE
      
      # Check if the grid position is part of the block
      return (grid_y, grid_x) in self.positions
      
    return False
      
  def start_drag(self, mouse_x, mouse_y):
    """Start dragging the block."""
    self.dragging = True
    self.drag_offset_x = mouse_x - self.x
    self.drag_offset_y = mouse_y - self.y
      
  def update_drag(self, mouse_x, mouse_y):
    """Update the block's position while dragging."""
    if self.dragging:
      self.x = mouse_x - self.drag_offset_x
      self.y = mouse_y - self.drag_offset_y
      
  def end_drag(self):
    """End dragging the block."""
    self.dragging = False
      
  def get_grid_positions(self, grid_offset_x, grid_offset_y):
    """Get the grid positions that this block occupies."""
    grid_positions = []
    for row, col in self.positions:
      grid_x = int((self.x + col * CELL_SIZE - grid_offset_x) // CELL_SIZE)
      grid_y = int((self.y + row * CELL_SIZE - grid_offset_y) // CELL_SIZE)
      # Only include positions that are within the grid boundaries
      if 0 <= grid_y < GRID_SIZE and 0 <= grid_x < GRID_SIZE:
        grid_positions.append((grid_y, grid_x))
    return grid_positions
      
  def snap_to_grid(self, grid_offset_x, grid_offset_y):
    """Snap the block to the nearest grid position."""
    grid_x = round((self.x - grid_offset_x) / CELL_SIZE) * CELL_SIZE + grid_offset_x
    grid_y = round((self.y - grid_offset_y) / CELL_SIZE) * CELL_SIZE + grid_offset_y
    self.x = grid_x
    self.y = grid_y
      
  def draw(self, screen, alpha=255, ghost=False):
    """Draw the block on the screen."""
    for row, col in self.positions:
      rect = pygame.Rect(
          self.x + col * CELL_SIZE,
          self.y + row * CELL_SIZE,
          CELL_SIZE,
          CELL_SIZE
      )
      
      if ghost:
        # Draw as a ghost using the tile image with transparency
        if self.color in TILE_IMAGES:
            # Create a surface for the ghost tile
            ghost_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            # Blit the tile image onto the ghost surface
            ghost_surface.blit(TILE_IMAGES[self.color], (0, 0))
            # Set the alpha for the entire surface
            ghost_surface.set_alpha(100)
            # Draw the ghost tile
            screen.blit(ghost_surface, rect)
        else:
            # Fallback to drawing a semi-transparent rectangle if no tile image
            color_with_alpha = (*self.color, 100)
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(s, color_with_alpha, (0, 0, CELL_SIZE, CELL_SIZE))
            screen.blit(s, rect)
      else:
        # Draw using the tile image if available, otherwise fall back to colored rectangle
        if self.color in TILE_IMAGES:
            screen.blit(TILE_IMAGES[self.color], rect)
        else:
            # Fallback to drawing a colored rectangle
            pygame.draw.rect(screen, self.color, rect)
            pygame.draw.rect(screen, BLACK, rect, 2)  # Border
