"""User settings for a project."""

# load the system configuration. You can override them in this module,
# but beware it might break stuff
from .sysconfig import *

## Customize these for all features

# PROJECT_SLUG = ""



## Admin

MOCK_HOME = '$HOME/tmp/refugue-tests/mock_home'

DEFAULT_USER_SPEC = 'tests/jigs/dev/users.toml'
SKEL_DIR = 'tests/jigs/dev/skel'
