"""
API key stored by unicode code points to avoid key being scrapped from github.

Should realistically restrict the key in the future instead of just rate limiting.
"""

KEY = '65_73_122_97_83_121_66_112_104_72_57_120_68_' \
      '114_105_109_103_101_100_75_79_82_118_105_50_' \
      '74_99_90_116_66_84_67_52_122_65_49_70_73_119'


def get_key() -> str:
    """Decodes and returns key stored by unicode code points."""
    result = ''
    for x in KEY.split('_'):
        result += chr(int(x))
    return result
