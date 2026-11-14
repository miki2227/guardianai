from pathlib import Path
import time
Path('/output/trigger').write_text('ok')
time.sleep(3)
Path('/output/late').write_text('bad')
