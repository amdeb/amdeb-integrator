# -*- coding: utf-8 -*-

"""
Event subscribers for product-related operations.
Odoo uses two tables to store product-related data:
product.template and product.product.
We need to subscribe both in write operation.
"""

import cPickle
import logging

from ..shared.model_names import PRODUCT_OPERATION_TABLE

from ..shared.record_operations import (
    CREATE_RECORD,
    WRITE_RECORD,
    UNLINK_RECORD,
)

_logger = logging.getLogger(__name__)


def create_record(model_name, env, record_id):
    record_values = {
        'record_id': record_id,
        'model_name': model_name,
        'record_operation': CREATE_RECORD,
    }
    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(record_values)
    return record


def write_record(model_name, env, record_id, values):
    """ Write a product write record for the model name """

    # product_template call write() after it creates a new database record
    # therefore it triggers write event first that should be ignored.
    # ignore a write operation that doesn't have a create operation

    data = cPickle.dumps(values, cPickle.HIGHEST_PROTOCOL)
    record_values = {
        'record_id': record_id,
        'model_name': model_name,
        'record_operation': WRITE_RECORD,
        'operation_data': data,
    }

    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(record_values)
    return record.id


def unlink_record(model_name, env, record_id):
    record_values = {
        'record_id': record_id,
        'model_name': model_name,
        'record_operation': UNLINK_RECORD,
    }

    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(record_values)
    return record.id
