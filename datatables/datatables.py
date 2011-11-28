import pkg_resources

from pylons import config
from pylons.i18n import get_lang, _
from paste.cascade import Cascade
from paste.urlparser import StaticURLParser
from paste.deploy.converters import asbool
from genshi.filters import Transformer
from genshi.input import HTML

from openspending import model
from openspending.lib import json
from openspending.ui.lib import helpers as h
from openspending.plugins.core import SingletonPlugin, implements
from openspending.plugins.interfaces import IMiddleware, IGenshiStreamFilter

HEAD_SNIPPET = """
<link rel="stylesheet" type="text/css" href="/css/data_tables.css" />
"""

JS_SNIPPET = """
<script src="/js/jquery.dataTables.min.js"></script>
<script src="/js/datatables.js"></script>
"""

TABLE_SNIPPET = """
<table cellpadding="0" cellspacing="0" border="0" class="data_table" id="data_table">
    <thead>
        <tr>
            <th>%(name)s</th>
            <th class="">%(amount)s</th>
            <th class="">%(percentage)s</th>
            <th class="">%(change)s</th>
        </tr>
    </thead>
    <tbody>
        %(rows)s
    </tbody>
</table>
"""

ROW_SNIPPET = """
        <tr>
            <td>%(name)s</td>
            <td class="num">%(amount)s</td>
            <td class="num">%(percentage)s</td>
            <td class="num">%(change)s</td>
        </tr>
"""

class DataTablesPlugin(SingletonPlugin):
    implements(IGenshiStreamFilter, inherit=True)
    implements(IMiddleware, inherit=True)

    def setup_middleware(self, app):
        if not isinstance(app, Cascade):
            log.warn("DataTablesPlugin expected the app to be a Cascade "
                     "object, but it wasn't. Not adding public paths for "
                     "Datatables, so it probably won't work!")
            return app

        max_age = None if asbool(config['debug']) else 3600
        public = pkg_resources.resource_filename(__name__, 'public')

        static_app = StaticURLParser(public, cache_max_age=max_age)

        app.apps.insert(0, static_app)

        return app

    def filter(self, stream):
        from pylons import tmpl_context as c
        if hasattr(c, 'viewstate') and hasattr(c, 'time'):
            if len(c.viewstate.aggregates):
                breakdown = c.view.drilldown
                dimension = c.dataset[breakdown]
                breakdown = dimension.label or breakdown

                columns = {
                    'name': _("Name"),
                    'amount': _("Amount (%s)") % c.view.dataset.currency,
                    'percentage': _("Percentage"),
                    'change': _("Change +/-"),
                    'breakdown': breakdown
                }
                rows = self._transform_rows(c.viewstate.aggregates,
                        c.dataset.name, dimension, c.time,
                        c.time_before, c.viewstate.totals)
                columns['rows'] = "\n".join([ROW_SNIPPET % row for row in rows])
                stream = stream | Transformer('html/head')\
                    .append(HTML(HEAD_SNIPPET))
                stream = stream | Transformer('html/body')\
                    .append(HTML(JS_SNIPPET))
                stream = stream | Transformer('//div[@id="detail"]')\
                    .after(HTML(TABLE_SNIPPET % columns))
        return stream

    def _transform_rows(self, aggregates, dataset, dimension, time, 
            time_before, totals):
        rows = []
        total = totals.get(time)
        #total_before = totals.get(time_before)
        for obj, values in aggregates:
            row = {}
            row['name'] = h.dimension_link(dataset, dimension.name, obj)
            value = values.get(time)
            if value is not None:
                row['amount'] = h.format_number_with_commas(value)
                row['value'] = value
            else:
                row['amount'] = '-'
                row['value'] = 0
            if total is not None and value is not None:
                share = abs(float(value))/max(1.0,abs(float(total))) * 100.0
                row['percentage'] = "%.2f%%" % share
            else:
                row['percentage'] = '-'
            before = values.get(time_before, 0.0)
            if (value is not None) and before > 0:
                change = ((value - before)/before) * 100
                if value >= before:
                    row['change'] = "<span class='growth'>+%.2f%%</span>" % change
                else:
                    row['change'] = "<span class='shrink'>%.2f%%</span>" % change
            else:
                row['change'] = '-'
            rows.append(row)
        return sorted(rows, key=lambda k: k['value'])


