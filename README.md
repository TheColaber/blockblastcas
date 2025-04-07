# Block Blast python3.11 main.py

A pygame-based puzzle game where you place blocks on an 8x8 grid to clear rows.

## Game Rules
- You have three random blocks to place on the grid
- Blocks must be placed in valid positions (not overlapping existing blocks or outside the grid)
- When a row or column is completely filled, it gets cleared (with a cool ripple animation!)
- Rows above do not shift down when a row is cleared
- You lose when you can't place any of your blocks
- Score increases based on blocks placed and rows cleared
- Maintain a multiplier streak by clearing rows within three moves

## Controls
- Click and drag blocks to place them on the grid
- A ghost preview shows where the block will be placed
- Invalid placements return blocks to their original position

## Setup
1. Install the required packages:
```
pip install -r requirements.txt
```

2. Run the game:
```
python main.py
```

Enjoy the game! 