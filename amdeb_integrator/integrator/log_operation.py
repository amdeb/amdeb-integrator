# -*- coding: utf-8 -*-


import cPickle
import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import PRODUCT_OPERATION_TABLE


def log_operation(env, operation_record):
    """ Log product operations. """

    values = ''
    if 'values' in operation_record:
        values = operation_record['values']
        dumped_values = cPickle.dumps(values, cPickle.HIGHEST_PROTOCOL)
        operation_record['operation_data'] = dumped_values
        operation_record.pop('values')

    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(operation_record)
    logger_template = "Model: {0}, record id: {1}, template id: {2}. " \
                      "operation: {3}, record id: {4}, values: {5}."
    _logger.debug(logger_template.format(
        operation_record['model_name'],
        operation_record['record_id'],
        operation_record['template_id'],
        operation_record['operation_type'],
        record.id,
        values
    ))
