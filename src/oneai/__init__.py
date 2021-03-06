__version__ = "0.4.7"
__package__ = "oneai"
__prefix__ = "\33[34m●\33[36m▲\33[35m▮\33[0m"

from typing_extensions import Final
import oneai.skills as skills
from oneai.classes import *
from oneai.pipeline import Pipeline
import oneai.clustering as clustering

URL: Final[str] = "https://api.oneai.com"
"""
Base URL for the pipeline API. Only change if you know what you're doing.
"""

api_key = None
"""
Default api key to use. You can use different keys for different pipelines by setting the `Pipeline.api_key` attribute or passing an `api_key` parameter to `Pipeline.run` calls.
"""

MAX_CONCURRENT_REQUESTS: Final[int] = 2
"""
Max number of allowed concurrent requests to be made by the SDK.
Currently only enforced on `pipeline.run_batch`, other calls may be limited by the API
"""
PRINT_PROGRESS = True
"""
Wether to print progress of batch processing in `Pipeline.run_batch` calls
"""
