# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from openerp import models, fields, api

from ..shared.model_names import (
    PRODUCT_OPERATION_TABLE,
    PRODUCT_PRODUCT,
    PRODUCT_TEMPLATE,
)
from ..shared.operations_types import (
    CREATE_RECORD,
    WRITE_RECORD,
    UNLINK_RECORD,
)

import logging
_logger = logging.getLogger(__name__)

_UNLINK_DAYS = 100


# there are some arguments when used as field default value
def field_utcnow(*args):
    """ Return the current UTC day and time in the format expected by the ORM.
        This function may be used to compute default values.
    """
    return datetime.utcnow().strftime(DATETIME_FORMAT)


class ProductOperation(models.Model):
    _name = PRODUCT_OPERATION_TABLE
    _description = 'Product Operation Log'
    _log_access = False

    model_name = fields.Selection(
        string='Model Name',
        required=True,
        selection=[(PRODUCT_PRODUCT, PRODUCT_PRODUCT),
                   (PRODUCT_TEMPLATE, PRODUCT_TEMPLATE),
                   ],
        readonly=True,
    )

    # don't use Many2One because we keep the record
    # even if the referred product is deleted
    record_id = fields.Integer(
        string='Record Id',
        required=True,
        index=True,
        readonly=True,
    )

    # we need to remember the product.template id in unlink
    template_id = fields.Integer(
        string='Product Template Id',
        required=True,
        index=True,
        readonly=True,
    )

    # the type of record operation such as create_record,
    # write_record or unlink_record
    record_operation = fields.Selection(
        string='Record Operation',
        required=True,
        selection=[(CREATE_RECORD, CREATE_RECORD),
                   (WRITE_RECORD, WRITE_RECORD),
                   (UNLINK_RECORD, UNLINK_RECORD),
                   ],
        readonly=True,
    )

    # the pickled record operation data
    # it is updating values in write
    # it is not set for create and unlink
    operation_data = fields.Binary(
        string='Operation Data',
        readonly=True,
    )

    timestamp = fields.Datetime(
        string='Operation Timestamp',
        required=True,
        default=field_utcnow,
        index=True,
        readonly=True,
    )

    def _get_old_records(self):
        now = datetime.utcnow()
        unlink_date = now - timedelta(days=_UNLINK_DAYS)
        unlink_date_str = unlink_date.strftime(DATETIME_FORMAT)
        return self.search([
            ('timestamp', '<', unlink_date_str)
        ])

    @api.model
    def cleanup_cron(self):
        _logger.info("Amdeb product operation cleanup cron job running.")

        unlink_records = self._get_old_records()
        unlink_count = len(unlink_records)
        unlink_records.unlink()

        _logger.info("Amdeb product operation cleaned {} records.".format(
            unlink_count
        ))
