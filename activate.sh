#!/bin/bash
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
elif [ -f "$HOME/frangilive/.venv/bin/activate" ]; then
  source "$HOME/frangilive/.venv/bin/activate"
fi
