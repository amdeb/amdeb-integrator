# -*- coding: utf-8 -*-

"""
    Intercept record change event by replacing Odoo record change functions
    with new functions. A new functions calls an original one and
    creates an operation record for integration.
    The new function signatures are copied from openerp/models.py
"""

import logging
from openerp import api, SUPERUSER_ID
from openerp.addons.product.product import product_template, product_product
from openerp.addons.stock.stock import stock_quant

from ..shared.model_names import (
    PRODUCT_OPERATION_TABLE,
    PRODUCT_TEMPLATE_ID_FIELD,
    PRODUCT_PRODUCT_TABLE,
    PRODUCT_TEMPLATE_TABLE,
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD,
    OPERATION_TYPE_FIELD,
    WRITE_FIELD_NAMES_FIELD,
    PRODUCT_VIRTUAL_AVAILABLE_FIELD,
)
from ..shared.operations_constants import (
    CREATE_RECORD,
    WRITE_RECORD,
    UNLINK_RECORD,
    FIELD_NAME_DELIMITER,
)

_logger = logging.getLogger(__name__)

# first save interested original methods
original_create = {
    PRODUCT_PRODUCT_TABLE: product_product.create,
    PRODUCT_TEMPLATE_TABLE: product_template.create,
}

original_write = {
    PRODUCT_PRODUCT_TABLE: product_product.write,
    PRODUCT_TEMPLATE_TABLE: product_template.write,
}
original_unlink = {
    PRODUCT_PRODUCT_TABLE: product_product.unlink,
    PRODUCT_TEMPLATE_TABLE: product_template.unlink,
}


def _set_template_id(self, product, operation_record):
    if self._name == PRODUCT_PRODUCT_TABLE:
        template_id = product[PRODUCT_TEMPLATE_ID_FIELD].id
        operation_record[TEMPLATE_ID_FIELD] = template_id


def log_operation(env, operation_record):
    """ Log product operations. """
    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(operation_record)
    logger_template = "New product operation Id: {0}, Model: {1}, " \
                      "record id: {2}, template id: {3}. " \
                      "operation type: {4}, values: {5}."
    _logger.debug(logger_template.format(
        record.id,
        operation_record[MODEL_NAME_FIELD],
        operation_record[RECORD_ID_FIELD],
        operation_record[TEMPLATE_ID_FIELD],
        operation_record[OPERATION_TYPE_FIELD],
        operation_record.get(WRITE_FIELD_NAMES_FIELD, None),
    ))


# To make this also work correctly for traditional-style call,
# We need to 1) override @api.returns defined in the BaseModel
# to support old-style api that returns an id
# and 2) check the return value type to get the id
@api.model
@api.returns('self', lambda value: value.id)
def create(self, values):
    original_method = original_create[self._name]
    record = original_method(self, values)

    operation_record = {
        MODEL_NAME_FIELD: self._name,
        RECORD_ID_FIELD: record.id,
        TEMPLATE_ID_FIELD: record.id,
        OPERATION_TYPE_FIELD: CREATE_RECORD,
    }

    _set_template_id(self, record, operation_record)
    env = self.env(user=SUPERUSER_ID)
    log_operation(env, operation_record)

    return record


@api.multi
def write(self, values):
    original_method = original_write[self._name]
    original_method(self, values)

    # sometimes value is empty, don't log it
    if values:
        field_names = FIELD_NAME_DELIMITER.join(values.keys())
        for product in self.browse(self.ids):
            operation_record = {
                MODEL_NAME_FIELD: self._name,
                RECORD_ID_FIELD: product.id,
                TEMPLATE_ID_FIELD: product.id,
                OPERATION_TYPE_FIELD: WRITE_RECORD,
                WRITE_FIELD_NAMES_FIELD: field_names,
            }
            _set_template_id(self, product, operation_record)
            env = self.env(user=SUPERUSER_ID)
            log_operation(env, operation_record)

    return True


def _create_unlink_data(self, cr, uid, ids, context):

    # product_template can be unlink 1) by unlink itself or
    # 2) by unlink its last product_product. However,
    # if there are more than one variants and we unlink
    # all variants in a single step, Odoo doesn't unlink product_template.
    # It only unlink product_template if we unlink the last
    # variant individually.

    unlink_records = []
    for product in self.browse(cr, uid, ids, context=context):
        operation_record = {
            MODEL_NAME_FIELD: self._name,
            RECORD_ID_FIELD: product.id,
            TEMPLATE_ID_FIELD: product.id,
            OPERATION_TYPE_FIELD: UNLINK_RECORD,
        }
        _set_template_id(self, product, operation_record)
        unlink_records.append(operation_record)

    return unlink_records


# To make it also work correctly for record-style call,
# we need to apply the decorator here
@api.cr_uid_ids_context
def unlink(self, cr, uid, ids, context=None):
    """ log unlink product's ean13 and default_code """

    # The context can not be None in our functions and in api.Environment
    if context is None:
        context = {}

    # save product data before unlink
    unlink_records = _create_unlink_data(self, cr, uid, ids, context)

    original_method = original_unlink[self._name]
    original_method(self, cr, uid, ids, context=context)

    env = api.Environment(cr, SUPERUSER_ID, context)
    for unlink_record in unlink_records:
        log_operation(env, unlink_record)
    return True

# replace with interceptors
product_product.create = create
product_template.create = create
product_product.write = write
product_template.write = write
product_product.unlink = unlink
product_template.unlink = unlink

# stock quantity create trigger, convert to product write
original_stock_quantity_create = stock_quant.create


@api.model
@api.returns('self', lambda value: value.id)
def new_stock_quantity_create(self, values):
    # convert stock quantity create into a product quantity write
    # it is related to a product variant only
    original_method = original_stock_quantity_create
    record = original_method(self, values)

    product_variant = record.product_id
    operation_record = {
        MODEL_NAME_FIELD: PRODUCT_PRODUCT_TABLE,
        RECORD_ID_FIELD: product_variant.id,
        TEMPLATE_ID_FIELD: product_variant[PRODUCT_TEMPLATE_ID_FIELD].id,
        OPERATION_TYPE_FIELD: WRITE_RECORD,
        WRITE_FIELD_NAMES_FIELD: PRODUCT_VIRTUAL_AVAILABLE_FIELD,
    }

    env = self.env(user=SUPERUSER_ID)
    log_operation(env, operation_record)

    return record

stock_quant.create = new_stock_quantity_create
