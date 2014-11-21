# -*- coding: utf-8 -*-

"""
    Intercept record change event by replacing Odoo record change functions
    with new functions. A new functions calls an original one and
    creates an operation record for integration.
    The new function signatures are copied from openerp/models.py
"""

import cPickle
import logging

from openerp import api, SUPERUSER_ID
from openerp.addons.product.product import product_template, product_product

from ..shared import utility
from ..shared.model_names import (
    PRODUCT_PRODUCT,
    PRODUCT_TEMPLATE,
    PRODUCT_OPERATION_TABLE,
)
from ..shared.operations_types import (
    CREATE_RECORD,
    WRITE_RECORD,
    UNLINK_RECORD,
)

_logger = logging.getLogger(__name__)


def log_operation(env, model_name, record_id,
                  template_id, values, operation_type):
    """ Log product operations. """

    if values:
        values = cPickle.dumps(values, cPickle.HIGHEST_PROTOCOL)

    record_values = {
        'model_name': model_name,
        'record_id': record_id,
        'template_id': template_id,
        'record_operation': operation_type,
        'operation_data': values,
    }

    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(record_values)
    _logger.debug("Model: {}, record id: {}, template id: {}. "
                  "{} operation: {}, record id {}, values: {}.".format(
        model_name, record_id, template_id,
        PRODUCT_OPERATION_TABLE, operation_type, record.id, values
    ))

# first save interested original methods
original_create = {
    PRODUCT_PRODUCT: product_product.create,
}

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

    template_id = record.id
    if self._name == PRODUCT_PRODUCT:
        template_id = record.product_tmpl_id.id

    env = self.env(user=SUPERUSER_ID)
    log_operation(env, self._name, record.id,
                  template_id, None, CREATE_RECORD)

    return record


@api.multi
def write(self, values):
    original_method = original_write[self._name]
    original_method(self, values)

    # sometimes value is empty, don't log it
    if values:
        for product in self.browse():
            template_id = product.id
            if self._name == PRODUCT_PRODUCT:
                template_id = product.product_tmpl_id.id

            env = self.env(user=SUPERUSER_ID)
            log_operation(env, self._name, product.id,
                          template_id, values, WRITE_RECORD)

    return True


# To make it also work correctly for record-style call,
# we need to apply the decorator here
@api.cr_uid_ids_context
def unlink(self, cr, uid, ids, context=None):
    """ log unlink product's ean13 and default_code """
    # product_template can be deleted 1) by itself or
    # 2) by deletion of its last product_product.
    # In the second case,  product_template unlink
    # doesn't have ean13 and default_code.
    # Therefore we need to to remember product_product's
    # template id to retrieve the ean13 and default_code.
    product_codes = {}
    for product in self.browse(cr, uid, ids, context=context):
        template_id = product.id
        if self._name == PRODUCT_PRODUCT:
            template_id = product.product_tmpl_id.id

        # for product_template unlinked by its last product_product,
        # its ean13 and default_code are False.
        product_codes[product.id] = (
            template_id,
            (product.ean13, product.default_code),
        )

    original_method = original_unlink[self._name]
    original_method(self, cr, uid, ids, context=context)

    if not utility.is_sequence(ids):
        ids = [ids]

    # The context can not be None for api.Environment
    if context is None:
        context = {}

    env = api.Environment(cr, SUPERUSER_ID, context)
    for record_id in product_codes:
        log_operation(
            env, self._name, record_id,
            product_codes[record_id][0],
            product_codes[record_id][1],
            UNLINK_RECORD
        )

    return True

# replace with interceptors
product_product.create = create
product_product.write = write
product_template.write = write
product_product.unlink = unlink
product_template.unlink = unlink
