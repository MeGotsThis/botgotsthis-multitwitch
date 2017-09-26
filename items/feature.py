from typing import Mapping, Optional


def features() -> Mapping[str, Optional[str]]:
    if not hasattr(features, 'features'):
        setattr(features, 'features', {
            'nomultitwitch': 'Disable !multitwitch',
            })
    return getattr(features, 'features')
