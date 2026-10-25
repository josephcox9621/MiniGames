# MiniGames

## Connect Four

Local two-player Connect Four built with Pygame. Run from the repository root:

```powershell
python -m pip install pygame-ce
python Game/main.py
```

Click a board column to drop a piece, or select a column with Left/Right and
drop with Space, Enter, or Down. Click **New game** or press **R** to restart.
Red starts. The game detects horizontal, vertical, and diagonal wins and draws.

The reusable `ConnectFour` class exposes `handle_event(event)`,
`update(delta_time)` (seconds), `draw()`, and `reset()` for a host game loop.
The launcher retains its asynchronous yield for pygbag compatibility.

Artwork is optional. See [the asset guide](Game/assets/connect_four/README.md)
for PNG placeholders to replace with your own pixel art.

Run the headless regression tests with:

```powershell
python -m unittest discover -s Game/tests -v
```