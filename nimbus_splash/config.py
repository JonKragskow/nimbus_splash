'''
Information on Nimbus configuration and ORCA module - instance compatibility
'''

# Current installed orca modules - 26/11/2024
ORCA_MODULES: dict[str, dict[str, str]] = {
    'fsv2': {
        '5.0.1': 'ORCA/5.0.1-gompi-2021a',
        '5.0.4': '/apps/x86_64/modules/all/ORCA/5.0.4',
        '6.0.0': '/apps/x86_64/modules/all/ORCA/6.0.0',
        '6.0.1': 'ORCA/6.0.1-gompi-2023b',
    },
    'hc': {
        '5.0.1': 'ORCA/5.0.1-gompi-2021a',
        '6.0.1': 'ORCA/6.0.1-gompi-2023a',
    },
    'hbv2': {
        '5.0.1': 'ORCA/5.0.1-gompi-2021a',
        '6.0.1': 'ORCA/6.0.1-gompi-2023a'
    },
    'hbv3': {
        '6.0.1': 'ORCA/6.0.1-gompi-2023a'
    }
}

# Instances which currently have an ORCA module available
ORCA_SUPPORTED_INSTANCES: list[str] = [
    'spot-fsv2-2',
    'spot-fsv2-4',
    'spot-fsv2-8',
    'spot-fsv2-16',
    'spot-fsv2-32',
    'paygo-fsv2-2',
    'paygo-fsv2-4',
    'paygo-fsv2-8',
    'paygo-fsv2-16',
    'paygo-fsv2-32',
    # 'paygo-hb-60',
    'paygo-hbv2-120',
    'paygo-hbv3-120',
    'paygo-hc-44',
    # 'paygo-ncv3-12',
    # 'paygo-ncv3-24',
    # 'paygo-ncv3-6',
    # 'paygo-ncv3r-24',
    # 'paygo-ndv2-40',
    # 'spot-hb-60',
    'spot-hbv2-120',
    'spot-hbv3-120',
    'spot-hc-44',
    # 'spot-ncv3-12',
    # 'spot-ncv3-24',
    # 'spot-ncv3-6',
    # 'spot-ncv3r-24',
    # 'spot-ndv2-40',
    # 'vis-ncv3-12',
    # 'vis-ncv3-24',
    # 'vis-ncv3-6',
    # 'vis-ndv2-40'
]

#: Total memory of each instance in MB
INSTANCE_TOTAL_MEM: dict[str, int] = {
    'fsv2-2': 3500 * 2,
    'fsv2-4': 3500 * 4,
    'fsv2-8': 3500 * 8,
    'fsv2-16': 3500 * 16,
    'fsv2-32': 3500 * 32,
    'spot-fsv2-2': 3500 * 2,
    'spot-fsv2-4': 3500 * 4,
    'spot-fsv2-8': 3500 * 8,
    'spot-fsv2-16': 3500 * 16,
    'spot-fsv2-32': 3500 * 32,
    'paygo-fsv2-2': 3500 * 2,
    'paygo-fsv2-4': 3500 * 4,
    'paygo-fsv2-8': 3500 * 8,
    'paygo-fsv2-16': 3500 * 16,
    'paygo-fsv2-32': 3500 * 32,
    'paygo-hbv2-120': 456000,
    'paygo-hbv3-120': 448000,
    'paygo-hc-44': 352000,
    'paygo-hb-60': 228000,
    'hbv2-120': 456000,
    'hbv3-120': 448000,
    'hc-44': 352000,
    'hb-60': 228000,
    # 'paygo-ncv3-6': 112000,
    # 'paygo-ncv3-12': 224000,
    # 'paygo-ncv3-24': 448000,
    # 'paygo-ncv3r-24': 18500,
    # 'paygo-ndv2-40': 672000,
    'spot-hbv2-120': 456000,
    'spot-hbv3-120': 448000,
    'spot-hb-60': 228000,
    'spot-hc-44': 352000,
    # 'spot-ncv3-6': 112000,
    # 'spot-ncv3-12': 224000,
    # 'spot-ncv3-24': 448000,
    # 'spot-ncv3r-24': 18500,
    # 'spot-ndv2-40': 672000,
    # 'vis-ncv3-6': 112000,
    # 'vis-ncv3-12': 224000,
    # 'vis-ncv3-24': 448000,
    # 'vis-ndv2-40': 672000
}

#: Total number of cores of each instance
INSTANCE_TOTAL_CORES: dict[str, int] = {
    'fsv2-2': 2,
    'fsv2-4': 4,
    'fsv2-8': 8,
    'fsv2-16': 16,
    'fsv2-32': 32,
    'hbv2-120': 120,
    'hbv3-120': 120,
    'hc-44': 44,
    'hb-60': 60,
    'spot-fsv2-2': 2,
    'spot-fsv2-4': 4,
    'spot-fsv2-8': 8,
    'spot-fsv2-16': 16,
    'spot-fsv2-32': 32,
    'paygo-fsv2-2': 2,
    'paygo-fsv2-4': 4,
    'paygo-fsv2-8': 8,
    'paygo-fsv2-16': 16,
    'paygo-fsv2-32': 32,
    'paygo-hbv2-120': 120,
    'paygo-hbv3-120': 120,
    'paygo-hc-44': 44,
    'paygo-hb-60': 60,
    'spot-hbv2-120': 120,
    'spot-hbv3-120': 120,
    'spot-hb-60': 60,
    'spot-hc-44': 44
}
