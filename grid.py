import time
import numpy as np
import pygame
from block import Block, TILE_IMAGES, load_tile_images
from constants import BLACK, CELL_SIZE, DARK_GRAY, GRID_SIZE, WHITE

class Grid:
  def __init__(self, width, height, offset_x, offset_y):
    self.width = width
    self.height = height
    self.offset_x = offset_x
    self.offset_y = offset_y
    # Initialize the grid as a 2D array of zeros
    self.cells = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
    self.cell_colors = np.zeros((GRID_SIZE, GRID_SIZE, 3), dtype=int)
    # For animation
    self.cleared_rows = []
    self.cleared_cols = []
    self.animation_start_time = 0
    
    # Load tile images if not already loaded
    if not TILE_IMAGES:
        load_tile_images()

  def is_valid_placement(self, block: Block):
    """Check if the block can be placed at its current position."""
    grid_positions = block.get_grid_positions(self.offset_x, self.offset_y)
    
    # Check if all cells are within the grid and not occupied
    if len(grid_positions) != len(block.positions):
      return False  # Some parts are outside the grid
        
    for row, col in grid_positions:
      # Ensure row and col are integers and within bounds
      row, col = int(row), int(col)
      if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
        return False  # Position is out of bounds
      if self.cells[row][col]:
        return False  # Cell is already occupied
            
    return True
          
  def place_block(self, block):
    """Place the block on the grid."""
    grid_positions = block.get_grid_positions(self.offset_x, self.offset_y)
    
    for row, col in grid_positions:
        self.cells[row][col] = True
        self.cell_colors[row][col] = block.color
        
    # Check for filled rows and columns
    self.check_filled_lines()

  def check_filled_lines(self):
    """Check for and mark filled rows and columns."""
    # Check rows
    for row in range(GRID_SIZE):
      if np.all(self.cells[row]):
        self.cleared_rows.append(row)
          
    # Check columns
    for col in range(GRID_SIZE):
      if np.all(self.cells[:, col]):
        self.cleared_cols.append(col)
          
    # If there are any cleared rows or columns, start the animation
    if self.cleared_rows or self.cleared_cols:
      self.animation_start_time = time.time()
      
  def update_animation(self):
    """Update the clearing animation."""
    if not (self.cleared_rows or self.cleared_cols):
      return False
        
    animation_duration = 1.0  # seconds
    elapsed_time = time.time() - self.animation_start_time
    
    if elapsed_time > animation_duration:
      # Animation finished, clear the rows/columns
      for row in self.cleared_rows:
        self.cells[row] = False
        self.cell_colors[row] = np.zeros((GRID_SIZE, 3), dtype=int)  # Reset colors to black (empty)
      
      for col in self.cleared_cols:
        self.cells[:, col] = False
        self.cell_colors[:, col] = np.zeros(3, dtype=int)  # Reset colors to black (empty)
          
      num_cleared = len(self.cleared_rows) + len(self.cleared_cols)
      self.cleared_rows = []
      self.cleared_cols = []
      return num_cleared
      
    return False
  
  def draw(self, screen):
    """Draw the grid and placed blocks."""
    # Draw grid background
    grid_rect = pygame.Rect(self.offset_x, self.offset_y, self.width, self.height)
    pygame.draw.rect(screen, DARK_GRAY, grid_rect)
    
    # Draw grid lines
    for i in range(GRID_SIZE + 1):
      # Vertical lines
      pygame.draw.line(
        screen, WHITE,
        (self.offset_x + i * CELL_SIZE, self.offset_y),
        (self.offset_x + i * CELL_SIZE, self.offset_y + self.height)
      )
      
      # Horizontal lines
      pygame.draw.line(
        screen, WHITE,
        (self.offset_x, self.offset_y + i * CELL_SIZE),
        (self.offset_x + self.width, self.offset_y + i * CELL_SIZE)
      )
        
    # Draw placed blocks and empty cells
    for row in range(GRID_SIZE):
      for col in range(GRID_SIZE):
        rect = pygame.Rect(
          self.offset_x + col * CELL_SIZE,
          self.offset_y + row * CELL_SIZE,
          CELL_SIZE,
          CELL_SIZE
        )
        
        # Check if this cell is in a cleared row or column
        is_clearing = row in self.cleared_rows or col in self.cleared_cols
        
        if self.cells[row][col]:
          if is_clearing:
            # Draw with ripple animation if in a cleared row/column
            elapsed_time = time.time() - self.animation_start_time
            animation_progress = min(elapsed_time, 1.0)
            
            # Ripple effect
            center_x = rect.centerx
            center_y = rect.centery
            distance_from_center = 0
            
            if row in self.cleared_rows:
                distance_from_center = abs(col - GRID_SIZE // 2)
            if col in self.cleared_cols:
                distance_from_center = max(distance_from_center, abs(row - GRID_SIZE // 2))
                
            delay = distance_from_center * 0.1
            cell_progress = max(0, min(1, (animation_progress - delay) * 2.5))
            
            if cell_progress < 1:
              scale = 1 - cell_progress
              new_width = int(CELL_SIZE * scale)
              new_height = int(CELL_SIZE * scale)
              new_rect = pygame.Rect(
                center_x - new_width // 2,
                center_y - new_height // 2,
                new_width,
                new_height
              )
              
              color = self.cell_colors[row][col]
              alpha = int(255 * (1 - cell_progress))
              
              # Convert NumPy array to tuple for dictionary lookup
              color_tuple = tuple(color)
              
              # Use tile image if available, otherwise fall back to colored rectangle
              if color_tuple in TILE_IMAGES:
                  # Create a surface with alpha channel
                  s = pygame.Surface((new_width, new_height), pygame.SRCALPHA)
                  
                  # Get the tile image and scale it
                  tile_img = TILE_IMAGES[color_tuple]
                  scaled_img = pygame.transform.scale(tile_img, (new_width, new_height))
                  
                  # Apply alpha to the scaled image
                  scaled_img.set_alpha(alpha)
                  
                  # Blit the scaled image onto the surface
                  s.blit(scaled_img, (0, 0))
                  
                  # Blit the surface onto the screen
                  screen.blit(s, new_rect)
              else:
                  # Fallback to colored rectangle with alpha
                  s = pygame.Surface((new_width, new_height), pygame.SRCALPHA)
                  s.fill((*color, alpha))
                  screen.blit(s, new_rect)
            else:
                # When animation is complete for this cell, show empty tile
                if None in TILE_IMAGES:
                    screen.blit(TILE_IMAGES[None], rect)
                else:
                    pygame.draw.rect(screen, DARK_GRAY, rect)
                    pygame.draw.rect(screen, BLACK, rect, 2)
          else:
            # Normal block drawing
            color = self.cell_colors[row][col]
            # Convert NumPy array to tuple for dictionary lookup
            color_tuple = tuple(color)
            # Use tile image if available, otherwise fall back to colored rectangle
            if color_tuple in TILE_IMAGES:
                screen.blit(TILE_IMAGES[color_tuple], rect)
            else:
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)  # Border
        else:
            # Draw empty cell using empty tile
            if None in TILE_IMAGES:
                screen.blit(TILE_IMAGES[None], rect)
            else:
                # Fallback to drawing a dark gray rectangle
                pygame.draw.rect(screen, DARK_GRAY, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)  # Border
