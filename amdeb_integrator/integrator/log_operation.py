# -*- coding: utf-8 -*-

import cPickle
import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    PRODUCT_OPERATION_TABLE,
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD,
    RECORD_OPERATION_FIELD,
    OPERATION_DATA_FIELD,
)


def log_operation(env, operation_record):
    """ Log product operations. """

    values = ''
    if 'values' in operation_record:
        values = operation_record['values']
        dumped_values = cPickle.dumps(values, cPickle.HIGHEST_PROTOCOL)
        operation_record[OPERATION_DATA_FIELD] = dumped_values
        operation_record.pop('values')

    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(operation_record)
    logger_template = "Model: {0}, record id: {1}, template id: {2}. " \
                      "operation: {3}, record id: {4}, values: {5}."
    _logger.debug(logger_template.format(
        operation_record[MODEL_NAME_FIELD],
        operation_record[RECORD_ID_FIELD],
        operation_record[TEMPLATE_ID_FIELD],
        operation_record[RECORD_OPERATION_FIELD],
        record.id,
        values
    ))
