# -*- coding: utf-8 -*-
# AutoSynthesis: The Automated Process Synthesis & Design package.
# Copyright (C) 2022-, Sarang Bhagwat <sarang.bhagwat.git@gmail.com>
# 
# This module is under the UIUC open-source license. See 
# https://github.com/sarangbhagwat/autosynthesis/blob/main/LICENSE
# for license details.
"""
"""

from .._process_block import ProcessBlock
from .feedstock_to_sugars import cane_juicing, corn_dry_grind, cellulosic_pretreatment_saccharification
from .sugar_fermentation import fermentation_HP, fermentation_TAL, fermentation_ethanol
from .product_separation import HP_solution_separation, TAL_separation, ethanol_separation
from .product_upgrading import HP_solution_upgrading_acrylic_acid, TAL_upgrading_potassium_sorbate
from._block_superstructure import BlockSuperstructure

__all__ = (
    'ProcessBlock',
    *cane_juicing.__all__,
    *corn_dry_grind.__all__,
    *cellulosic_pretreatment_saccharification.__all__,
    *fermentation_HP.__all__,
    *fermentation_TAL.__all__,
    *fermentation_ethanol.__all__,
    *HP_solution_separation.__all__,
    *TAL_separation.__all__,
    *ethanol_separation.__all__,
    *HP_solution_upgrading_acrylic_acid.__all__,
    *TAL_upgrading_potassium_sorbate.__all__,
    'BlockSuperstructure',
)
