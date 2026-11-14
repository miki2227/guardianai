from pathlib import Path
import time
Path('/workspace/private_token.txt').read_text()
time.sleep(3)
Path('/output/late').write_text('synthetic copied data')
