# -*- coding: utf-8 -*-

"""
    Intercept record change event by replacing Odoo record change functions
    with new functions. A new functions calls an original one and
    creates an operation record for integration.
    The new function signatures are copied from openerp/models.py
"""

from openerp import api, SUPERUSER_ID
from openerp.addons.product.product import product_template, product_product
from openerp.addons.stock.stock import stock_quant

from ..shared.model_names import (
    PRODUCT_TEMPLATE_ID_FIELD,
    PRODUCT_PRODUCT_TABLE,
    PRODUCT_TEMPLATE_TABLE,
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD,
    OPERATION_TYPE_FIELD,
    OPERATION_DATA_FIELD,
    PRODUCT_VIRTUAL_AVAILABLE_FIELD,
)
from ..shared.operations_types import (
    CREATE_RECORD,
    WRITE_RECORD,
    UNLINK_RECORD,
)
from .log_operation import log_operation

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

    if self._name == PRODUCT_PRODUCT_TABLE:
        template_id = record[PRODUCT_TEMPLATE_ID_FIELD].id
        operation_record[TEMPLATE_ID_FIELD] = template_id

    env = self.env(user=SUPERUSER_ID)
    log_operation(env, operation_record)

    return record


# image values are too big to track, change them to True
def _change_image_value(values):
    image_fields = ['image', 'image_medium', 'image_small']
    for image_field in image_fields:
        if image_field in values:
            values[image_field] = True


@api.multi
def write(self, values):
    original_method = original_write[self._name]
    original_method(self, values)

    # sometimes value is empty, don't log it
    if values:
        _change_image_value(values)
        for product in self.browse(self.ids):
            operation_record = {
                MODEL_NAME_FIELD: self._name,
                RECORD_ID_FIELD: product.id,
                TEMPLATE_ID_FIELD: product.id,
                OPERATION_TYPE_FIELD: WRITE_RECORD,
                OPERATION_DATA_FIELD: values,
            }
            if self._name == PRODUCT_PRODUCT_TABLE:
                template_id = product[PRODUCT_TEMPLATE_ID_FIELD].id
                operation_record[TEMPLATE_ID_FIELD] = template_id

            env = self.env(user=SUPERUSER_ID)
            log_operation(env, operation_record)

    return True

_context_key_prefix = "template_unlink"


def _check_last_variant(self, cr, uid, context, operation_record):
    """ create a product_template unlink data for the last variant """

    # the last variant unlink operation also unlink its
    # product_template
    # Check if this is the last variant of its template
    # code is copied from product.py
    record_id = operation_record[RECORD_ID_FIELD]
    template_id = operation_record[TEMPLATE_ID_FIELD]
    other_product_ids = self.search(
        cr, uid,
        [(PRODUCT_TEMPLATE_ID_FIELD, '=', template_id),
         ('id', '!=', record_id)],
        context=context
    )
    if not other_product_ids:
        # the last product_product, set product_template unlink data
        operation_record[MODEL_NAME_FIELD] = PRODUCT_TEMPLATE_TABLE
        operation_record[RECORD_ID_FIELD] = template_id

        # notice later product_template unlink using context flag
        # thus not to create another unlink operation record
        context_key = _context_key_prefix + str(template_id)
        context[context_key] = True


def _create_unlink_data(self, cr, uid, ids, context):

    # product_template can be unlink 1) by unlink itself or
    # 2) by unlink inside its last product_product unlink.
    # In the second case,  product_template unlink
    # doesn't have ean13 and default_code.
    # Therefore we create product_template unlink
    # record when the last product_product is unlinked

    # If there are more than one variants and we unlink
    # all in a single call, Odoo doesn't unlink product_template.
    # It only unlink product_template if we only unlink the last
    # variant in its own unlink call.

    unlink_records = []
    for product in self.browse(cr, uid, ids, context=context):
        operation_record = {
            MODEL_NAME_FIELD: self._name,
            RECORD_ID_FIELD: product.id,
            TEMPLATE_ID_FIELD: product.id,
            OPERATION_TYPE_FIELD: UNLINK_RECORD,
            OPERATION_DATA_FIELD: (product.ean13, product.default_code),
        }

        if self._name == PRODUCT_PRODUCT_TABLE:
            template_id = product[PRODUCT_TEMPLATE_ID_FIELD].id
            operation_record[TEMPLATE_ID_FIELD] = template_id
            # update unlink data if it is the last product variant
            _check_last_variant(self, cr, uid, context, operation_record)
        else:
            # We don't create unlink data for product_template unlink
            # when its unlink data is created by its last variant
            context_key = _context_key_prefix + str(product.id)
            if context.get(context_key, None):
                continue

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
    original_method = original_stock_quantity_create
    record = original_method(self, values)

    product_variant = record.product_id
    operation_record = {
        MODEL_NAME_FIELD: PRODUCT_PRODUCT_TABLE,
        RECORD_ID_FIELD: product_variant.id,
        TEMPLATE_ID_FIELD: product_variant[PRODUCT_TEMPLATE_ID_FIELD].id,
        OPERATION_TYPE_FIELD: WRITE_RECORD,
        OPERATION_DATA_FIELD: {PRODUCT_VIRTUAL_AVAILABLE_FIELD: record.qty},
    }

    env = self.env(user=SUPERUSER_ID)
    log_operation(env, operation_record)

    return record

stock_quant.create = new_stock_quantity_create
