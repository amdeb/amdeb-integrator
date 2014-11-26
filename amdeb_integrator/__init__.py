# -*- coding: utf-8 -*-

# need to load models used by views and security files
# use relative import path here because
# Odoo add prefix to module name
from . import models

# import trigger to intercept record change operations
from . import integrator
