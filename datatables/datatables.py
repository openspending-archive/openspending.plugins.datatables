import pkg_resources
import logging

from pylons import config
from pylons.i18n import _
from paste.cascade import Cascade
from paste.urlparser import StaticURLParser
from paste.deploy.converters import asbool
from genshi.filters import Transformer
from genshi.input import HTML

from openspending.ui.lib import helpers as h
from openspending.plugins.core import SingletonPlugin, implements
from openspending.plugins.interfaces import IMiddleware, IGenshiStreamFilter

JS_SNIPPET = """
<script src="/jstables/jquery.tablesorter.min.js"></script>
<script>
    $(function() {
        $("table#data-table").tablesorter({ sortList: [[2,1]] });
    });
</script>
"""

TABLE_SNIPPET = """
<table cellpadding="0" cellspacing="0" border="0" class="zebra-striped" id="data-table">
    <thead>
        <tr>
            <th>%(name)s</th>
            <th class="num">%(amount)s</th>
            <th class="num">%(percentage)s</th>
            <th class="num">%(change)s</th>
        </tr>
    </thead>
    <tbody>
        %(rows)s
    </tbody>
</table>
"""

log = logging.getLogger(__name__)

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
                dimension = c.dataset[c.view.drilldown]
                columns = {
                    'name': _("Name"),
                    'amount': _("Amount (%s)") % c.view.dataset.currency,
                    'percentage': _("Percentage"),
                    'change': _("Change +/-")
                }
                rows = self._transform_rows(c.viewstate.aggregates,
                        c.dataset.name, dimension, c.time,
                        c.time_before, c.viewstate.totals)
                columns['rows'] = "\n".join([ROW_SNIPPET % row for row in rows])
                stream = stream | Transformer('html/body')\
                    .append(HTML(JS_SNIPPET))
                stream = stream | Transformer('//div[@id="detail"]')\
                    .after(HTML(TABLE_SNIPPET % columns))
        return stream

    def _transform_rows(self, aggregates, dataset, dimension, time, 
            time_before, totals):
        rows = []
        total = totals.get(time)
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
                    row['change'] = "<span class='growth'>%.2f%%</span>" % change
                else:
                    row['change'] = "<span class='shrink'>%.2f%%</span>" % change
            else:
                row['change'] = '-'
            rows.append(row)
        return sorted(rows, key=lambda k: -1 * k['value'])


