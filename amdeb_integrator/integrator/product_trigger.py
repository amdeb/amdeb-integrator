# -*- coding: utf-8 -*-

"""
    Intercept record change event by replacing Odoo record change functions
    with new functions. A new functions calls an original one and
    creates an operation record for integration.
    The new function signatures are copied from openerp/models.py
"""

from openerp import api, SUPERUSER_ID
from openerp.addons.product.product import product_template, product_product

from ..shared import utility
from ..shared.model_names import PRODUCT_PRODUCT, PRODUCT_TEMPLATE
from .log_product_operation import (
    log_create_operation,
    log_write_operation,
    log_unlink_operation,
)

# first save interested original methods
original_create = {PRODUCT_PRODUCT: product_product.create,}
original_write = {
    PRODUCT_PRODUCT: product_product.write,
    PRODUCT_TEMPLATE: product_template.write,
    }
original_unlink = {
    PRODUCT_PRODUCT: product_product.unlink,
    PRODUCT_TEMPLATE: product_template.unlink,
    }


# To make this also work correctly for traditional-style call,
# We need to 1) override @api.returns defined in the BaseModel
# to support old-style api that returns an id
# and 2) check the return value type to get the id
@api.model
@api.returns('self', lambda value: value.id)
def create(self, values):
    original_method = original_create[self._name]
    record = original_method(self, values)
    env = self.env(user=SUPERUSER_ID)
    log_create_operation(self._name, env, record.id)

    return record


@api.multi
def write(self, values):
    original_method = original_write[self._name]
    original_method(self, values)

    #sometimes value is empty, don't log it
    if values:
        env = self.env(user=SUPERUSER_ID)
        for record_id in self._ids:
            log_write_operation(self._name, env, record_id, values)

    return True


# To make it also work correctly for record-style call,
# we need to apply the decorator here
@api.cr_uid_ids_context
def unlink(self, cr, uid, ids, context=None):
    original_method = original_unlink[self._name]
    original_method(self, cr, uid, ids, context=context)

    if not utility.is_sequence(ids):
        ids = [ids]

    # The context can not be None for api.Environment
    if context is None:
        context = {}

    env = api.Environment(cr, SUPERUSER_ID, context)
    for record_id in ids:
        log_unlink_operation(self._name, env, record_id)

    return True

# replace with interceptors
product_product.create = create
product_product.write = write
product_template.write = write
product_product.unlink = unlink
product_template.unlink = unlink
