# -*- coding: utf-8 -*-


import cPickle
import logging

from ..shared.model_names import PRODUCT_OPERATION_TABLE

_logger = logging.getLogger(__name__)


class OperationRecord(object):
    """ Used to store operation record data """

    def __init__(self, model_name=None, record_id=None,
                 template_id=None, values=None,
                 operation_type=None):
        self.model_name = model_name
        self.record_id = record_id
        self.template_id = template_id
        self.values = values
        self.operation_type = operation_type


def log_operation(env, operation_record):
    """ Log product operations. """

    dumped_values = cPickle.dumps(
        operation_record.values, cPickle.HIGHEST_PROTOCOL)

    record_values = {
        'model_name': operation_record.model_name,
        'record_id': operation_record.record_id,
        'template_id': operation_record.template_id,
        'operation_data': dumped_values,
        'record_operation': operation_record.operation_type,
    }

    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(record_values)
    logger_template = "Model: {0}, record id: {1}, template id: {2}. " \
                      "{3} operation: {4}, record id {5}, values: {6}."
    _logger.debug(logger_template.format(
        operation_record.model_name,
        operation_record.record_id,
        operation_record.template_id,
        PRODUCT_OPERATION_TABLE,
        operation_record.operation_type,
        record.id,
        operation_record.values
    ))
