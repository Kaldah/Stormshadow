# sip-only-stormshadow
 
You can run the tool like this:
Example : 
 python3 main.py --mode both --attack-name invite-flood --max_count 1 --open_window

# Note: the program now self-elevates when root is required.
# You can run it without sudo; it will restart itself with sudo and
# keep your current virtualenv and environment variables.

# More examples
python3 main.py --mode both --attack-name invite-flood --open_window
python3 main.py --mode gui

# Optional: manual sudo (not required anymore)
sudo /home/kaldah/venvs/scratchpad/bin/python3 main.py --mode both --attack-name invite-flood --open_window