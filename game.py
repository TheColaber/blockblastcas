import random
import sys
import pygame
import numpy as np
import math
import os

from block import BLOCK_TYPES, Block
from grid import Grid
from constants import BLACK, CELL_SIZE, GRAY, GRID_HEIGHT, GRID_OFFSET_X, GRID_OFFSET_Y, GRID_SIZE, GRID_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH


class Game:
  def __init__(self):
    self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Block Blast")
    self.clock = pygame.time.Clock()
    self.font = pygame.font.SysFont(None, 36)
    self.small_font = pygame.font.SysFont(None, 24)
    
    # Load custom font
    try:
        self.custom_font = pygame.font.Font('ZenDots-Regular.ttf', 48)  # Bigger font size
        self.small_custom_font = pygame.font.Font('ZenDots-Regular.ttf', 24)  # Smaller font for multiplier
    except Exception as e:
        print(f"Could not load custom font: {e}")
        self.custom_font = self.font  # Fallback to default font
        self.small_custom_font = self.small_font
    
    # Initialize and play background music
    pygame.mixer.init()
    
    try:
        if os.path.exists('bgmusic.wav'):
            pygame.mixer.music.load('bgmusic.wav')
            pygame.mixer.music.set_volume(0.5)  # Set volume to 50%
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
    except Exception as e:
        print(f"Could not load music: {e}")
    
    self.grid = Grid(GRID_WIDTH, GRID_HEIGHT, GRID_OFFSET_X, GRID_OFFSET_Y)
    self.available_blocks = self.generate_blocks()
    self.selected_block = None
    self.original_positions = []
    
    self.score = 0
    self.displayed_score = 0  # For score animation
    self.score_animation_speed = 1  # Base animation speed
    self.multiplier = 1
    self.moves_since_clear = 0
    self.game_over = False
    self.animation_in_progress = False
    self.last_score_update = 0  # Track when the score was last updated
      
  def generate_blocks(self):
      """Generate three random blocks with different types."""
      blocks: list[Block] = []
      used_types = set()
      
      # Get all block types
      block_types = list(BLOCK_TYPES.keys())
      
      # Generate three blocks
      for _ in range(3):
          # Choose a random block type that hasn't been used yet
          available_types = [t for t in block_types if t not in used_types]
          if not available_types:
              available_types = block_types  # If all types have been used, use any type
              
          block_type = random.choice(available_types)
          used_types.add(block_type)
          
          # Create the block
          block = Block(block_type)
          
          # Position the block in the available blocks area
          block.set_position(WINDOW_WIDTH - 320, 50 + len(blocks) * 200)
          
          blocks.append(block)
      
      # Store the original positions of the blocks
      self.original_positions = [(block.x, block.y) for block in blocks]
      
      return blocks
      
  def reset_block_positions(self):
      """Reset blocks to their original positions."""
      for i, block in enumerate(self.available_blocks):
          block.set_position(*self.original_positions[i])
          
  def check_game_over(self, after_clears=False):
      """Check if any block can be placed on the grid.
      
      Args:
          after_clears: If True, simulate the board state after blocks are cleared
      """
      print("\nChecking game over state:")
      print(f"Number of available blocks: {len(self.available_blocks)}")
      
      # Create a temporary grid to simulate the state
      temp_grid = Grid(GRID_WIDTH, GRID_HEIGHT, GRID_OFFSET_X, GRID_OFFSET_Y)
      
      # Copy the current grid state
      temp_grid.cells = self.grid.cells.copy()
      temp_grid.cell_colors = self.grid.cell_colors.copy()
      
      print("Current grid state:")
      print(temp_grid.cells)
      
      # If simulating after clears, check for rows and columns to clear
      if after_clears:
          # Check for filled rows and columns
          rows_to_clear = []
          cols_to_clear = []
          
          # Check rows
          for row in range(GRID_SIZE):
              if np.all(temp_grid.cells[row]):
                  rows_to_clear.append(row)
                  
          # Check columns
          for col in range(GRID_SIZE):
              if np.all(temp_grid.cells[:, col]):
                  cols_to_clear.append(col)
                  
          # Clear the rows and columns
          for row in rows_to_clear:
              temp_grid.cells[row] = False
              
          for col in cols_to_clear:
              temp_grid.cells[:, col] = False
              
          print("Grid state after clears:")
          print(temp_grid.cells)
      
      # Check if any block can be placed on the grid
      for block in self.available_blocks:
          print(f"\nChecking block with positions: {block.positions}")
          # Try all possible positions on the grid
          original_pos = (block.x, block.y)
          
          can_place = False
          for row in range(GRID_SIZE):
              for col in range(GRID_SIZE):
                  # Check if the block would fit within the grid boundaries
                  max_row = max(r for r, _ in block.positions)
                  max_col = max(c for _, c in block.positions)
                  if row + max_row >= GRID_SIZE or col + max_col >= GRID_SIZE:
                      continue
                      
                  block.set_position(
                      self.grid.offset_x + col * CELL_SIZE,
                      self.grid.offset_y + row * CELL_SIZE
                  )
                  
                  # Check if placement is valid on the temporary grid
                  grid_positions = block.get_grid_positions(self.grid.offset_x, self.grid.offset_y)
                  valid = True
                  for r, c in grid_positions:
                      if r < 0 or r >= GRID_SIZE or c < 0 or c >= GRID_SIZE or temp_grid.cells[r][c]:
                          valid = False
                          break
                          
                  if valid:
                      can_place = True
                      print(f"Valid placement found at ({row}, {col})")
                      break
              if can_place:
                  break
                  
          # Restore original position
          block.set_position(*original_pos)
          
          if can_place:
              return False  # At least one block can be placed
              
      print("\nNo blocks can be placed - GAME OVER")
      return True  # No block can be placed
      
  def check_potential_clears(self, block):
    """Check which rows and columns would be cleared if the block is placed."""
    # Create a temporary grid to simulate placing the block
    temp_grid = Grid(GRID_WIDTH, GRID_HEIGHT, GRID_OFFSET_X, GRID_OFFSET_Y)
    
    # Copy the current grid state
    temp_grid.cells = self.grid.cells.copy()
    temp_grid.cell_colors = self.grid.cell_colors.copy()
    
    # Place the block on the temporary grid
    grid_positions = block.get_grid_positions(self.grid.offset_x, self.grid.offset_y)
    for row, col in grid_positions:
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            temp_grid.cells[row][col] = True
            temp_grid.cell_colors[row][col] = block.color
    
    # Check for filled rows and columns
    potential_rows = []
    potential_cols = []
    
    # Check rows
    for row in range(GRID_SIZE):
        if np.all(temp_grid.cells[row]):
            potential_rows.append(row)
            
    # Check columns
    for col in range(GRID_SIZE):
        if np.all(temp_grid.cells[:, col]):
            potential_cols.append(col)
            
    return potential_rows, potential_cols
  
  def draw_ghost_preview(self):
    """Draw a ghost preview of where the block would be placed."""
    if self.selected_block and not self.game_over:
        # Save original position
        original_x, original_y = self.selected_block.x, self.selected_block.y
        
        # Snap to grid for preview
        grid_x = ((self.selected_block.x - self.grid.offset_x) // CELL_SIZE) * CELL_SIZE + self.grid.offset_x
        grid_y = ((self.selected_block.y - self.grid.offset_y) // CELL_SIZE) * CELL_SIZE + self.grid.offset_y
        self.selected_block.set_position(grid_x, grid_y)
        
        # Draw ghost if placement is valid
        is_valid = self.grid.is_valid_placement(self.selected_block)
        if is_valid:
            # Check for potential row/column clears
            potential_rows, potential_cols = self.check_potential_clears(self.selected_block)
            
            # Draw the ghost block
            self.selected_block.draw(self.screen, ghost=True)
            
            # Calculate pulsing effect based on time
            pulse_value = (pygame.time.get_ticks() % 1000) / 1000.0  # Value between 0 and 1
            pulse_alpha = int(50 + 100 * abs(math.sin(pulse_value * math.pi)))  # Pulsing between 50 and 150
            
            # Highlight rows that would be cleared
            for row in potential_rows:
                # Draw a more visible highlight with pulsing effect
                highlight_rect = pygame.Rect(
                    self.grid.offset_x,
                    self.grid.offset_y + row * CELL_SIZE,
                    GRID_WIDTH,
                    CELL_SIZE
                )
                
                # Draw a bright border around the row
                border_rect = pygame.Rect(
                    self.grid.offset_x - 2,
                    self.grid.offset_y + row * CELL_SIZE - 2,
                    GRID_WIDTH + 4,
                    CELL_SIZE + 4
                )
                pygame.draw.rect(self.screen, (255, 255, 0), border_rect, 2)  # Thinner border
                
                # Draw a semi-transparent fill with pulsing alpha
                s = pygame.Surface((GRID_WIDTH, CELL_SIZE), pygame.SRCALPHA)
                s.fill((255, 255, 0, pulse_alpha))  # Yellow highlight with pulsing alpha
                self.screen.blit(s, highlight_rect)
                
            # Highlight columns that would be cleared
            for col in potential_cols:
                # Draw a more visible highlight with pulsing effect
                highlight_rect = pygame.Rect(
                    self.grid.offset_x + col * CELL_SIZE,
                    self.grid.offset_y,
                    CELL_SIZE,
                    GRID_HEIGHT
                )
                
                # Draw a bright border around the column
                border_rect = pygame.Rect(
                    self.grid.offset_x + col * CELL_SIZE - 2,
                    self.grid.offset_y - 2,
                    CELL_SIZE + 4,
                    GRID_HEIGHT + 4
                )
                pygame.draw.rect(self.screen, (255, 255, 0), border_rect, 2)  # Thinner border
                
                # Draw a semi-transparent fill with pulsing alpha
                s = pygame.Surface((CELL_SIZE, GRID_HEIGHT), pygame.SRCALPHA)
                s.fill((255, 255, 0, pulse_alpha))  # Yellow highlight with pulsing alpha
                self.screen.blit(s, highlight_rect)
                
        # Restore original position
        self.selected_block.set_position(original_x, original_y)
  
  def run(self):
      """Run the game loop."""
      running = True
      
      while running:
          # Check for game over at the beginning of each loop
          if not self.game_over and not self.animation_in_progress:
              print("Checking for game over...")
              if self.check_game_over():
                  print("Game over detected!")
                  self.game_over = True
              
          # Handle events
          for event in pygame.event.get():
              if event.type == pygame.QUIT:
                  running = False
                  
              if not self.game_over:
                  if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                      # Check if a block was clicked
                      mouse_x, mouse_y = pygame.mouse.get_pos()
                      for block in self.available_blocks:
                          if block.contains_point(mouse_x, mouse_y):
                              self.selected_block = block
                              block.start_drag(mouse_x, mouse_y)
                              break
                              
                  elif event.type == pygame.MOUSEMOTION:
                      # Update the selected block's position when dragging
                      if self.selected_block and self.selected_block.dragging:
                          mouse_x, mouse_y = pygame.mouse.get_pos()
                          self.selected_block.update_drag(mouse_x, mouse_y)
                          
                  elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                      # Place the block if it's a valid position
                      if self.selected_block and self.selected_block.dragging:
                          self.selected_block.end_drag()
                          
                          # Snap to grid
                          self.selected_block.snap_to_grid(self.grid.offset_x, self.grid.offset_y)
                          
                          if self.grid.is_valid_placement(self.selected_block):
                              # Place the block
                              self.grid.place_block(self.selected_block)
                              
                              # Update score
                              cells_in_block = len(self.selected_block.positions)
                              self.score += cells_in_block
                              self.last_score_update = pygame.time.get_ticks()  # Record when score was updated
                              print(f"Score updated: {self.score} (displayed: {self.displayed_score})")
                              
                              # Remove from available blocks
                              self.available_blocks.remove(self.selected_block)
                              
                              # Check if all blocks are placed
                              if not self.available_blocks:
                                  self.available_blocks = self.generate_blocks()
                                  
                              # Increment moves since last clear
                              self.moves_since_clear += 1
                              
                              # Reset multiplier and streak if no clear within 3 moves
                              if self.moves_since_clear > 3:
                                  print(f"Resetting multiplier and streak (moves since clear: {self.moves_since_clear})")
                                  self.multiplier = 1
                              
                              # Check for game over after potential clears
                              if self.check_game_over(after_clears=True):
                                  self.game_over = True
                          else:
                              # Invalid placement, return to original position
                              idx = self.available_blocks.index(self.selected_block)
                              if idx < len(self.original_positions):
                                  self.selected_block.set_position(*self.original_positions[idx])
                              else:
                                  # Fallback if original position is not available
                                  self.selected_block.set_position(WINDOW_WIDTH - 320, 50 + idx * 200)
                              
                          self.selected_block = None
              
              # Restart game on 'R' key press
              if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                  self.__init__()
                  
          # Update animations and check for cleared lines
          cleared_count = self.grid.update_animation()
          if cleared_count:
              # Animation is complete
              self.animation_in_progress = False
              
              # Update score and multiplier
              if self.multiplier == 1:
                  # Starting a new streak
                  self.multiplier = cleared_count + 1
              else:
                  # Continue the streak
                  self.multiplier += cleared_count
                  
              self.score += (cleared_count ** 2) * self.multiplier * 10
              self.last_score_update = pygame.time.get_ticks()  # Record when score was updated
              print(f"Score after clear: {self.score} (displayed: {self.displayed_score}, multiplier: {self.multiplier})")
              self.moves_since_clear = 0
              
              # Check for game over after blocks are cleared
              if self.check_game_over():
                  self.game_over = True
          elif self.grid.cleared_rows or self.grid.cleared_cols:
              # Animation is in progress
              self.animation_in_progress = True
              
          # Animate score - ensure it's updated every frame
          if self.displayed_score < self.score:
              # Calculate the step size based on the difference and current multiplier
              diff = self.score - self.displayed_score
              # Scale animation speed with multiplier, minimum of 1
              current_animation_speed = max(1, self.score_animation_speed * self.multiplier)
              step = max(1, min(current_animation_speed, diff))
              self.displayed_score += step
              
              # Only print every 100ms to avoid spam
              current_time = pygame.time.get_ticks()
              if current_time - self.last_score_update > 100:
                  print(f"Animating score: {self.displayed_score}/{self.score} (diff: {diff}, step: {step}, speed: {current_animation_speed})")
                  self.last_score_update = current_time
              
          # Drawing
          self.screen.fill(GRAY)
          
          # Draw grid
          self.grid.draw(self.screen)
          
          # Draw ghost preview
          self.draw_ghost_preview()
          
          # Draw available blocks
          for block in self.available_blocks:
              block.draw(self.screen)
              
          # Draw UI elements
          score_text = self.custom_font.render(f"{int(self.displayed_score)}", True, BLACK)
          text_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 50))  # Moved down to y=50
          self.screen.blit(score_text, text_rect)
          
          # Draw multiplier in bottom right of score
          multiplier_text = self.small_custom_font.render(f"x{self.multiplier}", True, BLACK)
          multiplier_rect = multiplier_text.get_rect(midleft=(text_rect.right + 10, text_rect.centery))
          self.screen.blit(multiplier_text, multiplier_rect)
          
          # Draw game over message
          if self.game_over:
              game_over_text = self.font.render("GAME OVER! Press R to restart", True, (255, 0, 0))
              text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
              self.screen.blit(game_over_text, text_rect)
              
          pygame.display.flip()
          self.clock.tick(60)
          
      pygame.quit()
      sys.exit()