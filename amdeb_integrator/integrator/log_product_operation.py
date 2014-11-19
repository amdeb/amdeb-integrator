# -*- coding: utf-8 -*-

"""
Create records for product-related operations.
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


def log_create_operation(model_name, env, record_id):
    record_values = {
        'record_id': record_id,
        'model_name': model_name,
        'record_operation': CREATE_RECORD,
    }

    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(record_values)
    _logger.debug("{} create record id {}. {} record id {}.".format(
        model_name, record_id, PRODUCT_OPERATION_TABLE, record.id
    ))

    return record


def log_write_operation(model_name, env, record_id, values):
    data = cPickle.dumps(values, cPickle.HIGHEST_PROTOCOL)
    record_values = {
        'record_id': record_id,
        'model_name': model_name,
        'record_operation': WRITE_RECORD,
        'operation_data': data,
    }

    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(record_values)
    _logger.debug("Model {} write record id {}. {} record id {}.".format(
        model_name, record_id, PRODUCT_OPERATION_TABLE, record.id
    ))

    return record.id


def log_unlink_operation(model_name, env, record_id):
    record_values = {
        'record_id': record_id,
        'model_name': model_name,
        'record_operation': UNLINK_RECORD,
    }

    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(record_values)
    _logger.debug("Model {} unlink record id {}. {} record id {}.".format(
        model_name, record_id, PRODUCT_OPERATION_TABLE, record.id
    ))

    return record.id
