from dataclasses import dataclass


@dataclass
class NetSettings:

    prompt_timed_out = 60 * 15
    """Timeout in seconds. If reached, the prompt is cancelled.
    Default: 
        15 Minutes
    """
