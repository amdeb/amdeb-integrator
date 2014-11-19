# -*- coding: utf-8 -*-

"""
    Intercept record change event by replacing Odoo record change functions
    with new functions. A new functions calls an original one and fires
    an event. The new function signatures are copied from openerp/models.py
"""

from openerp import api, SUPERUSER_ID
from openerp.addons.product.product import product_template, product_product

from ..shared import utility
from ..shared.model_names import PRODUCT_PRODUCT
from .record_producer import (
    create_record,
    write_record,
    unlink_record,
)

# first save old methods
original_create = product_product.create
original_write = product_product.write
original_unlink = product_product.unlink
original_template_unlink = product_template.unlink


# To make this also work correctly for traditional-style call,
# We need to 1) override @api.returns defined in the BaseModel
# to support old-style api that returns an id
# and 2) check the return value type to get the id
@api.model
@api.returns('self', lambda value: value.id)
def create(self, values):
    # _logger.debug("In create record for model: {} values: {}".format(
    #    self._name, values))

    # because we use the record-style api,
    # the return is always an record
    record = original_create(self, values)
    env = self.env(user=SUPERUSER_ID)
    create_record(self._name, env, record.id)

    return record


@api.multi
def write(self, values):
    # _logger.debug("In write record for model: {} ids: {}".format(
    #   self._name, self._ids))

    original_write(self, values)

    # many times values is empty, skip it
    if values:
        env = self.env(user=SUPERUSER_ID)
        for record_id in self._ids:
            write_record(self._name, env, record_id, values)

    return True


# To make it also work correctly for record-style call,
# we need to apply the decorator here
@api.cr_uid_ids_context
def unlink(self, cr, uid, ids, context=None):
    # _logger.debug("In unlink record for model: {} ids: {}".format(
    #    self._name, ids))

    if self._name == PRODUCT_PRODUCT:
        original_unlink(self, cr, uid, ids, context=context)
    else:
        original_template_unlink(self, cr, uid, ids, context=context)

    if not utility.is_sequence(ids):
        ids = [ids]

    if context is None:
        context = {}

    env = api.Environment(cr, SUPERUSER_ID, context)
    for record_id in ids:
       unlink_record(self._name, env, record_id)

    return True

# replace with interceptors
product_product.create = create
product_product.write = write
product_product.unlink = unlink
product_template.unlink = unlink
