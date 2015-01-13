# -*- coding: utf-8 -*-
# The SKU is probably used by more than one integrators
# thus we add it here

from openerp import models, fields
from ..shared.model_names import PRODUCT_TEMPLATE_TABLE, PRODUCT_PRODUCT_TABLE


class ProductTemplate(models.Model):
    _inherit = [PRODUCT_TEMPLATE_TABLE]

    # a template always has a SKU
    product_sku = fields.Char(
        string="Product SKU",
        help="Product SKU is a unique identifier for each distinct product.",
        index=True,
    )


class ProductProduct(models.Model):
    _inherit = [PRODUCT_PRODUCT_TABLE]

    # only non-partial variant has a SKU, this field is hidden
    # for partial variant
    product_sku = fields.Char(
        string="Product SKU",
        help="Product SKU is a unique identifier for each distinct product.",
        index=True,
    )
